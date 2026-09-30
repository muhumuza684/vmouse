import 'dart:async';
import 'package:flutter/material.dart';
import '../services/connection_service.dart';

class SystemControlScreen extends StatefulWidget {
  const SystemControlScreen({super.key});

  @override
  State<SystemControlScreen> createState() => _SystemControlScreenState();
}

class _SystemControlScreenState extends State<SystemControlScreen> {
  final _conn = ConnectionService();
  StreamSubscription<bool>? _statusSub;
  bool _connected = false;
  bool _busy = false;
  String? _commandOutput;
  final _commandController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _connected = _conn.connected;
    _statusSub = _conn.connectionStatus.listen((isConnected) {
      if (mounted) setState(() => _connected = isConnected);
    });
  }

  @override
  void dispose() {
    _statusSub?.cancel();
    _commandController.dispose();
    super.dispose();
  }

  void _confirmPower(String action) {
    if (!_connected) {
      _snack('Not connected to PC');
      return;
    }
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: const Color(0xFF111120),
        title: Text('Confirm ${action.toUpperCase()}', style: const TextStyle(color: Colors.white)),
        content: Text(
          'Are you sure you want to $action your PC?',
          style: const TextStyle(color: Color(0xFF8888aa)),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel', style: TextStyle(color: Color(0xFF8888aa))),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              _conn.send({'type': 'system_power', 'action': action});
              _snack('Sent: $action');
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: action == 'shutdown' ? const Color(0xFFEF4444) : const Color(0xFF6C5CE7),
              foregroundColor: Colors.white,
            ),
            child: Text('Yes, $action'),
          ),
        ],
      ),
    );
  }

  Future<void> _runCommand() async {
    final command = _commandController.text.trim();
    if (command.isEmpty) {
      _snack('Enter a command first');
      return;
    }
    setState(() {
      _busy = true;
      _commandOutput = null;
    });
    final response = await _conn.sendAndWait({'type': 'system_command', 'command': command});
    if (!mounted) return;
    setState(() {
      _busy = false;
      final status = response['status'];
      if (status == 'success') {
        final out = (response['output'] as String?)?.trim();
        _commandOutput = (out == null || out.isEmpty) ? 'Done (no output)' : out;
      } else if (status == 'blocked') {
        _commandOutput = 'Blocked: ${response['message']}';
      } else {
        _commandOutput = 'Error: ${response['message'] ?? 'Unknown error'}';
      }
    });
    _commandController.clear();
  }

  void _snack(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        elevation: 0,
        title: const Text('System Controls', style: TextStyle(color: Colors.white)),
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _statusPill(),
            const SizedBox(height: 20),
            const Text('Power', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 15)),
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(child: _powerButton('Shutdown', Icons.power_settings_new, const Color(0xFFEF4444), 'shutdown')),
                const SizedBox(width: 10),
                Expanded(child: _powerButton('Restart', Icons.restart_alt, const Color(0xFF6C5CE7), 'restart')),
              ],
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(child: _powerButton('Sleep', Icons.bedtime, const Color(0xFF2D2D4E), 'sleep')),
                const SizedBox(width: 10),
                Expanded(child: _powerButton('Lock', Icons.lock, const Color(0xFF2D2D4E), 'lock')),
              ],
            ),
            const SizedBox(height: 28),
            const Text('Diagnostic Command', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 15)),
            const SizedBox(height: 4),
            const Text(
              'Restricted to a read-only allow-list on the server (ipconfig, tasklist, ping, ...)',
              style: TextStyle(color: Color(0xFF8888aa), fontSize: 11),
            ),
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
              decoration: BoxDecoration(
                color: const Color(0xFF111120),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: const Color(0xFF1E1E32)),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _commandController,
                      style: const TextStyle(color: Colors.white, fontSize: 14),
                      decoration: const InputDecoration(
                        hintText: 'e.g. ipconfig',
                        hintStyle: TextStyle(color: Color(0xFF444466), fontSize: 13),
                        border: InputBorder.none,
                      ),
                      onSubmitted: (_) => _runCommand(),
                    ),
                  ),
                  IconButton(
                    icon: _busy
                        ? const SizedBox(
                            width: 18, height: 18,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF6C5CE7)),
                          )
                        : const Icon(Icons.play_arrow, color: Color(0xFF6C5CE7)),
                    onPressed: _busy ? null : _runCommand,
                  ),
                ],
              ),
            ),
            if (_commandOutput != null) ...[
              const SizedBox(height: 14),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFF0D0D1A),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFF1E1E32)),
                ),
                child: Text(
                  _commandOutput!,
                  style: const TextStyle(color: Color(0xFFCFCFEA), fontFamily: 'monospace', fontSize: 12),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _statusPill() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: _connected ? const Color(0xFF0D2E1A) : const Color(0xFF2E0D0D),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: _connected ? const Color(0xFF00C853) : const Color(0xFFFF1744)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 6, height: 6,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: _connected ? const Color(0xFF00C853) : const Color(0xFFFF1744),
            ),
          ),
          const SizedBox(width: 6),
          Text(
            _connected ? 'Connected' : 'PC Offline',
            style: TextStyle(
              color: _connected ? const Color(0xFF00C853) : const Color(0xFFFF1744),
              fontSize: 12, fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  Widget _powerButton(String label, IconData icon, Color color, String action) {
    return GestureDetector(
      onTap: () => _confirmPower(action),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14),
        decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(14)),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 16, color: Colors.white),
            const SizedBox(width: 6),
            Text(label, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13)),
          ],
        ),
      ),
    );
  }
}
