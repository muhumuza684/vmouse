import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';

/// One WebSocket connection, shared across the whole app for the life of
/// the session — connected once after the QR scan, and reused by every
/// screen (Mouse, Keyboard, System, Health) instead of each screen opening
/// and closing its own. Navigating between screens no longer drops and
/// re-establishes the connection.
class ConnectionService {
  static final ConnectionService _instance = ConnectionService._internal();
  factory ConnectionService() => _instance;
  ConnectionService._internal();

  WebSocketChannel? _channel;
  String? wsUrl;
  bool connected = false;

  Timer? _heartbeatTimer;
  Timer? _pingTimeoutTimer;

  final StreamController<dynamic> _messageController = StreamController<dynamic>.broadcast();
  final StreamController<bool> _connectionController = StreamController<bool>.broadcast();

  /// Every decoded (non-pong) message from the server, for screens that
  /// want to react to replies (System Controls, Health Monitor).
  Stream<dynamic> get messages => _messageController.stream;

  /// Fires whenever connected state changes — screens use this to update
  /// their "Connected / PC Offline" indicator without owning the socket.
  Stream<bool> get connectionStatus => _connectionController.stream;

  void connect(String url) {
    if (connected && wsUrl == url) return; // already connected to this URL
    disconnect();
    wsUrl = url;
    try {
      _channel = WebSocketChannel.connect(Uri.parse(url));
      _channel!.stream.listen(
        (msg) {
          if (msg == 'pong') {
            _pingTimeoutTimer?.cancel();
            return;
          }
          try {
            _messageController.add(jsonDecode(msg));
          } catch (_) {}
        },
        onDone: _onDisconnected,
        onError: (_) => _onDisconnected(),
      );
      connected = true;
      _connectionController.add(true);
      _startHeartbeat();
    } catch (_) {
      _onDisconnected();
    }
  }

  void _onDisconnected() {
    if (!connected) return; // avoid duplicate "disconnected" events
    connected = false;
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
    _channel?.sink.close();
    _channel = null;
    wsUrl = null;
    if (connected) {
      connected = false;
      _connectionController.add(false);
    }
  }
}
