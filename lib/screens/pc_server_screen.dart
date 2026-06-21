import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:qr_flutter/qr_flutter.dart';
import '../services/pc_server.dart';
import '../services/windows_input.dart';

class PCServerScreen extends StatefulWidget {
  const PCServerScreen({super.key});

  @override
  State<PCServerScreen> createState() => _PCServerScreenState();
}

class _PCServerScreenState extends State<PCServerScreen>
    with WidgetsBindingObserver {  // <-- observe lifecycle
  late final PcServer _server;
  String? _ip;
  String _status = 'Starting server…';
  int _clients = 0;
  final List<String> _logs = [];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _server = PcServer(
      onLog: (msg) {
        if (mounted) setState(() {
          _logs.insert(0, msg);
          if (_logs.length > 6) _logs.removeLast();
        });
      },
      onClientCountChanged: (count) {
        if (!mounted) return;
        setState(() {
          _clients = count;
          _status = count > 0 ? 'Phone connected ✓' : 'Waiting for phone…';
        });
      },
    );
    _start();
  }

  // Keep server running even when app loses focus / is minimized
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    // Do nothing — server keeps running regardless of window state
  }

  Future<void> _start() async {
    await WindowsInput.init();
    final ip = await _server.start();
    if (!mounted) return;
    setState(() {
      _ip = ip;
      _status = ip != null ? 'Waiting for phone…' : 'Failed to start server';
    });
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _server.stop();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final url = _ip != null ? 'ws://$_ip:8765' : '';
    return Scaffold(
      backgroundColor: Colors.black,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            children: [
              Row(children: [
                SizedBox(
                  width: 48,
                  child: Navigator.canPop(context)
                      ? IconButton(
                          onPressed: () => Navigator.pop(context),
                          icon: const Icon(Icons.arrow_back, color: Colors.white),
                        )
                      : null,
                ),
                Expanded(
                  child: Text('VMouse Server',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.white.withOpacity(0.6), fontSize: 13)),
                ),
                const SizedBox(width: 48),
              ]),
              const SizedBox(height: 24),
              Row(mainAxisSize: MainAxisSize.min, children: [
                Container(
                  width: 10, height: 10,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: _clients > 0 ? const Color(0xFF00D68F) : const Color(0xFFFF5C6A),
                    boxShadow: _clients > 0
                        ? [BoxShadow(color: const Color(0xFF00D68F).withOpacity(0.5), blurRadius: 8)]
                        : [],
                  ),
                ),
                const SizedBox(width: 10),
                Text(_status,
                    style: const TextStyle(color: Colors.white, fontSize: 17, fontWeight: FontWeight.w600)),
              ]),
              const SizedBox(height: 8),
              Text('Keep this window open — minimize with taskbar, don\'t close it',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.white.withOpacity(0.35), fontSize: 11)),
              const SizedBox(height: 28),
              if (_ip != null) ...[
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(20),
                    boxShadow: [
                      BoxShadow(color: const Color(0xFF6C5CE7).withOpacity(0.25), blurRadius: 40, spreadRadius: 4),
                    ],
                  ),
                  child: QrImageView(data: url, size: 200, backgroundColor: Colors.white),
                ),
                const SizedBox(height: 20),
                GestureDetector(
                  onTap: () {
                    Clipboard.setData(ClipboardData(text: _ip!));
                    ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('IP copied to clipboard')));
                  },
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                    decoration: BoxDecoration(
                      color: const Color(0xFF111120),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: const Color(0xFF2A2A4A)),
                    ),
                    child: Row(mainAxisSize: MainAxisSize.min, children: [
                      Text(_ip!,
                          style: const TextStyle(color: Colors.white, fontFamily: 'monospace', fontSize: 15)),
                      const SizedBox(width: 10),
                      const Icon(Icons.copy, color: Colors.white54, size: 15),
                    ]),
                  ),
                ),
              ] else if (_status.contains('Failed')) ...[
                const Icon(Icons.error_outline, color: Colors.redAccent, size: 48),
                const SizedBox(height: 14),
                Text(_status, style: const TextStyle(color: Colors.redAccent)),
              ] else ...[
                const CircularProgressIndicator(color: Color(0xFF6C5CE7)),
              ],
              const Spacer(),
              // Activity log
              if (_logs.isNotEmpty)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0A0A12),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: const Color(0xFF1E1E32)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: _logs.map((l) => Text(l,
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.5),
                        fontSize: 11,
                        fontFamily: 'monospace',
                      ))).toList(),
                  ),
                ),
              const SizedBox(height: 8),
            ],
          ),
        ),
      ),
    );
  }
}
