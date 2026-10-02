import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:web_socket_channel/io.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

/// One WebSocket connection, shared across the whole app for the life of
/// the session — connected once after the QR scan, and reused by every
/// screen (Mouse, Keyboard, System, Health) instead of each screen opening
/// and closing its own.
///
/// The QR code shown on the PC is a pairing link:
///   http://<pc-ip>:8080/?k=<pairing code>&wss=8765&ws=8766&fp=<sha1>&tls=1
/// The app connects over TLS (wss), checks that the PC's certificate matches
/// the fingerprint from the QR code, then sends the pairing code first.
class ConnectionService {
  static final ConnectionService _instance = ConnectionService._internal();
  factory ConnectionService() => _instance;
  ConnectionService._internal();

  WebSocketChannel? _channel;
  String? wsUrl;
  bool connected = false;

  /// Plain-language reason for the last failed connection, for screens to show.
  String? lastError;

  String? _token;
  String _fingerprint = '';
  bool _awaitingAuth = false;

  Timer? _heartbeatTimer;
  Timer? _pingTimeoutTimer;
  Timer? _authTimer;

  final StreamController<dynamic> _messageController = StreamController<dynamic>.broadcast();
  final StreamController<bool> _connectionController = StreamController<bool>.broadcast();

  /// Every decoded (non-pong) message from the server, for screens that
  /// want to react to replies (System Controls, Health Monitor).
  Stream<dynamic> get messages => _messageController.stream;

  /// Fires whenever connected state changes — screens use this to update
  /// their "Connected / PC Offline" indicator without owning the socket.
  Stream<bool> get connectionStatus => _connectionController.stream;

  /// Connect using whatever the QR code contained: a pairing link
  /// (http://ip:8080/?k=...) or, for older PC versions, a plain ws:// address.
  void connectFromQr(String raw) {
    final text = raw.trim();
    final uri = Uri.tryParse(text);
    if (uri == null) return;
    if (uri.scheme == 'ws' || uri.scheme == 'wss') {
      _token = null;
      _fingerprint = '';
      connect(text);
      return;
    }
    final token = uri.queryParameters['k'];
    if (token == null || token.isEmpty || uri.host.isEmpty) return;
    final useTls = uri.queryParameters['tls'] != '0';
    final portText = uri.queryParameters[useTls ? 'wss' : 'ws'] ?? '';
    final port = int.tryParse(portText) ?? (useTls ? 8765 : 8766);
    _token = token;
    _fingerprint = (uri.queryParameters['fp'] ?? '').toLowerCase();
    connect('${useTls ? 'wss' : 'ws'}://${uri.host}:$port');
  }

  HttpClient _pinnedClient() {
    final client = HttpClient();
    client.badCertificateCallback = (X509Certificate cert, String host, int port) {
      final expected = _fingerprint;
      if (expected.isEmpty) return false;
      final actual = cert.sha1.map((b) => b.toRadixString(16).padLeft(2, '0')).join();
      return actual == expected;
    };
    return client;
  }

  void connect(String url) {
    if ((connected || _awaitingAuth) && wsUrl == url) return; // already connecting/connected
    disconnect();
    wsUrl = url;
    lastError = null;
    try {
      final uri = Uri.parse(url);
      final secure = url.startsWith('wss://');
      _channel = secure
          ? IOWebSocketChannel.connect(uri, customClient: _pinnedClient())
          : WebSocketChannel.connect(uri);
      _channel!.stream.listen(
        _onMessage,
        onDone: _onDisconnected,
        onError: (_) => _onDisconnected(),
      );
      final token = _token;
      if (token != null) {
        _awaitingAuth = true;
        _channel!.sink.add(jsonEncode({'type': 'auth', 'token': token}));
        _authTimer?.cancel();
        _authTimer = Timer(const Duration(seconds: 10), () {
          if (_awaitingAuth) {
            lastError = 'The PC did not answer. Check that both devices use the same Wi-Fi.';
            disconnect();
          }
        });
      } else {
        _setConnected();
      }
    } catch (_) {
      _awaitingAuth = _token != null;
      lastError ??= 'Could not connect. Scan the QR code again.';
      _onDisconnected();
    }
  }

  void _setConnected() {
    connected = true;
    _connectionController.add(true);
    _startHeartbeat();
  }

  void _onMessage(dynamic msg) {
    if (msg == 'pong') {
      _pingTimeoutTimer?.cancel();
      return;
    }
    dynamic decoded;
    try {
      decoded = jsonDecode(msg as String);
    } catch (_) {
      return;
    }
    if (decoded is Map<String, dynamic>) {
      final type = decoded['type'];
      if (type == 'pong') {
        _pingTimeoutTimer?.cancel();
        return;
      }
      if (type == 'auth_ok') {
        _authTimer?.cancel();
        _awaitingAuth = false;
        _setConnected();
        return;
      }
      if (type == 'auth_failed') {
        _authTimer?.cancel();
        lastError = 'This PC did not accept the code. Scan the QR code on the PC again.';
        disconnect();
        return;
      }
    }
    _messageController.add(decoded);
  }

  void _onDisconnected() {
    _authTimer?.cancel();
    if (_awaitingAuth && lastError == null) {
      lastError = 'Could not reach the PC. Check the Wi-Fi and scan the QR code again.';
    }
    if (!connected && !_awaitingAuth) return; // avoid duplicate "disconnected" events
    connected = false;
    _awaitingAuth = false;
    _connectionController.add(false);
    _heartbeatTimer?.cancel();
    _pingTimeoutTimer?.cancel();
  }

  void _startHeartbeat() {
    _heartbeatTimer?.cancel();
    _heartbeatTimer = Timer.periodic(const Duration(seconds: 5), (_) {
      send({'type': 'ping'});
      _pingTimeoutTimer?.cancel();
      _pingTimeoutTimer = Timer(const Duration(seconds: 10), _onDisconnected);
    });
  }

  void send(Map<String, dynamic> data) {
    try {
      _channel?.sink.add(jsonEncode(data));
    } catch (_) {}
  }

  /// Send a command and resolve with the next message received — used by
  /// System Controls / Health Monitor for request/response calls (e.g.
  /// "run this diagnostic command", "get health"). Since only one request
  /// like this is ever in flight from the UI at a time, matching on "the
  /// next message" is reliable in practice.
  Future<Map<String, dynamic>> sendAndWait(
    Map<String, dynamic> command, {
    Duration timeout = const Duration(seconds: 10),
  }) {
    if (!connected) {
      return Future.value({'status': 'error', 'message': 'Not connected'});
    }
    final completer = Completer<Map<String, dynamic>>();
    late StreamSubscription sub;
    sub = messages.listen((data) {
      if (!completer.isCompleted && data is Map<String, dynamic>) {
        completer.complete(data);
        sub.cancel();
      }
    });
    send(command);
    return completer.future.timeout(
      timeout,
      onTimeout: () {
        sub.cancel();
        return {'status': 'error', 'message': 'Request timed out'};
      },
    );
  }

  /// Called when the person explicitly wants to reconnect (tapping the QR
  /// icon to scan a different PC) — closes the socket and clears state so
  /// the next connect() starts clean rather than being treated as a no-op.
  void disconnect() {
    _heartbeatTimer?.cancel();
    _pingTimeoutTimer?.cancel();
    _authTimer?.cancel();
    _channel?.sink.close();
    _channel = null;
    wsUrl = null;
    if (connected || _awaitingAuth) {
      connected = false;
      _awaitingAuth = false;
      _connectionController.add(false);
    }
  }
}
