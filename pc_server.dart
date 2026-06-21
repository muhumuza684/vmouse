import 'dart:convert';
import 'dart:io';
import 'windows_input.dart';

/// A WebSocket server that listens for commands from the VMouse phone app
/// and executes them as real mouse/keyboard input on this PC.
///
/// This runs entirely inside the Flutter app — no separate Python process
/// is needed.
class PcServer {
  HttpServer? _server;
  final List<WebSocket> _clients = [];
  final void Function(String message)? onLog;
  final void Function(int clientCount)? onClientCountChanged;

  PcServer({this.onLog, this.onClientCountChanged});

  /// Starts the server and returns this PC's local IP address,
  /// or null if the server failed to start.
  Future<String?> start({int port = 8765}) async {
    try {
      _server = await HttpServer.bind(InternetAddress.anyIPv4, port);
    } catch (e) {
      onLog?.call('Failed to start server: $e');
      return null;
    }

    _server!.listen((HttpRequest request) async {
      if (WebSocketTransformer.isUpgradeRequest(request)) {
        final socket = await WebSocketTransformer.upgrade(request);
        _clients.add(socket);
        onClientCountChanged?.call(_clients.length);
        onLog?.call('Phone connected');
        socket.listen(
          (data) => _handleMessage(socket, data),
          onDone: () {
            _clients.remove(socket);
            onClientCountChanged?.call(_clients.length);
            onLog?.call('Phone disconnected');
          },
          onError: (_) {
            _clients.remove(socket);
            onClientCountChanged?.call(_clients.length);
          },
        );
      } else {
        request.response.statusCode = HttpStatus.forbidden;
        await request.response.close();
      }
    });

    return _localIp();
  }

  Future<void> _handleMessage(WebSocket socket, dynamic raw) async {
    try {
      final data = jsonDecode(raw as String) as Map<String, dynamic>;
      final type = data['type'];
      switch (type) {
        case 'move':
          WindowsInput.moveRelative(
            (data['dx'] ?? 0) as int,
            (data['dy'] ?? 0) as int,
          );
          break;
        case 'click':
          WindowsInput.click(
            (data['button'] ?? 'left') as String,
            (data['clicks'] ?? 1) as int,
          );
          onLog?.call('Click: ${data['button'] ?? 'left'}');
          break;
        case 'scroll':
          WindowsInput.scroll((data['dy'] ?? 0) as int);
          break;
        case 'hotkey':
          final keys = (data['keys'] as List).map((e) => e.toString()).toList();
          WindowsInput.hotkey(keys);
          onLog?.call('Hotkey: ${keys.join('+')}');
          break;
        case 'keypress':
          if (data['text'] != null) {
            final text = data['text'] as String;
            await WindowsInput.typeText(text);
            socket.add(jsonEncode({'type': 'echo', 'status': 'sent', 'text': text}));
            onLog?.call('Typed: $text');
          } else if (data['key'] != null) {
            WindowsInput.keypress(data['key'] as String);
            onLog?.call('Key: ${data['key']}');
          }
          break;
      }
    } catch (e) {
      onLog?.call('Bad command: $e');
    }
  }

  Future<String> _localIp() async {
    final interfaces = await NetworkInterface.list(
      type: InternetAddressType.IPv4,
      includeLoopback: false,
    );
    for (final iface in interfaces) {
      for (final addr in iface.addresses) {
        if (!addr.isLoopback) return addr.address;
      }
    }
    return '127.0.0.1';
  }

  int get clientCount => _clients.length;

  Future<void> stop() async {
    for (final c in List<WebSocket>.from(_clients)) {
      await c.close();
    }
    _clients.clear();
    await _server?.close(force: true);
    _server = null;
  }
}
