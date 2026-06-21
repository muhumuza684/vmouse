import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:vibration/vibration.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../widgets/bottom_bar.dart';
import '../widgets/drawer_panel.dart';

class TrackpadScreen extends StatefulWidget {
  final String ip;
  const TrackpadScreen({super.key, required this.ip});

  @override
  State<TrackpadScreen> createState() => _TrackpadScreenState();
}

class _TrackpadScreenState extends State<TrackpadScreen> {
  WebSocketChannel? _channel;
  bool _connected = false;
  String _log = 'Connecting...';
  String _echo = '';
  double _sensitivity = 1.5;
  bool _drawerOpen = false;
  String _activeTab = 'type';

  double _lastX = 0, _lastY = 0;
  bool _dragging = false;
  int _fingerCount = 0;
  DateTime _touchStart = DateTime.now();
  bool _hintGone = false;

  @override
  void initState() {
    super.initState();
    _connect();
    _loadPrefs();
  }

  Future<void> _loadPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() => _sensitivity = prefs.getDouble('sensitivity') ?? 1.5);
  }

  void _connect() {
    try {
      _channel = WebSocketChannel.connect(Uri.parse('ws://${widget.ip}:8765'));
      _channel!.stream.listen(
        (msg) {
          final data = jsonDecode(msg);
          if (data['type'] == 'echo') {
            setState(() => _echo = '${data['status']}: "${data['text']}"');
            Future.delayed(const Duration(seconds: 3), () {
              if (mounted) setState(() => _echo = '');
            });
          }
        },
        onDone: () => setState(() { _connected = false; _log = 'Disconnected'; }),
        onError: (_) => setState(() { _connected = false; _log = 'Connection failed'; }),
      );
      setState(() { _connected = true; _log = 'Connected ✓'; });
    } catch (e) {
      setState(() { _connected = false; _log = 'Cannot connect: $e'; });
    }
  }

  void _send(Map<String, dynamic> data) {
    if (_connected) _channel?.sink.add(jsonEncode(data));
  }

  void _vibrate(int ms) async {
    if (await Vibration.hasVibrator() ?? false) Vibration.vibrate(duration: ms);
  }

  void _setLog(String msg) => setState(() => _log = msg);

  @override
  void dispose() {
    _channel?.sink.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: SafeArea(
        child: Stack(children: [
          Column(children: [
            _buildHeader(),
            Expanded(child: _buildTrackpad()),
            VMBottomBar(
              onLeftClick: () { _send({'type':'click','button':'left','clicks':1}); _setLog('Left click'); _vibrate(30); },
              onDoubleClick: () { _send({'type':'click','button':'left','clicks':2}); _setLog('Double click'); _vibrate(40); },
              onRightClick: () { _send({'type':'click','button':'right','clicks':1}); _setLog('Right click'); _vibrate(30); },
              onVoice: () => _setLog('Voice — use HTTPS for mic'),
              onDrawer: () => setState(() => _drawerOpen = true),
              logText: _log,
            ),
          ]),

          // Drawer overlay
          if (_drawerOpen) ...[
            GestureDetector(
              onTap: () => setState(() => _drawerOpen = false),
              child: Container(color: Colors.black.withOpacity(0.6)),
            ),
            Align(
              alignment: Alignment.bottomCenter,
              child: VMDrawerPanel(
                activeTab: _activeTab,
                sensitivity: _sensitivity,
                echoText: _echo,
                onTabChange: (t) => setState(() => _activeTab = t),
                onClose: () => setState(() => _drawerOpen = false),
                onSend: _send,
                onSensitivityChange: (v) async {
                  setState(() => _sensitivity = v);
                  final prefs = await SharedPreferences.getInstance();
                  await prefs.setDouble('sensitivity', v);
                },
                onHotkey: (keys) {
                  _send({'type': 'hotkey', 'keys': keys});
                  _setLog('Hotkey: ${keys.join('+')}');
                  _vibrate(25);
                },
                onKeypress: (key) {
                  _send({'type': 'keypress', 'key': key});
                  _setLog('Key: $key');
                  _vibrate(20);
                },
              ),
            ),
          ],
        ]),
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      decoration: const BoxDecoration(
        color: Color(0xFF0A0A12),
        border: Border(bottom: BorderSide(color: Color(0xFF1E1E32))),
      ),
      child: Row(children: [
        Container(
          width: 8, height: 8,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: _connected ? const Color(0xFF00D68F) : const Color(0xFFFF5C6A),
            boxShadow: _connected ? [BoxShadow(color: const Color(0xFF00D68F).withOpacity(0.5), blurRadius: 6)] : [],
          ),
        ),
        const SizedBox(width: 8),
        Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(_connected ? 'Connected' : 'Disconnected',
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: Colors.white)),
          Text('ws://${widget.ip}:8765',
            style: TextStyle(fontSize: 10, color: Colors.white.withOpacity(0.4), fontFamily: 'monospace')),
        ]),
        const Spacer(),
        ShaderMask(
          shaderCallback: (b) => const LinearGradient(
            colors: [Color(0xFF6C5CE7), Color(0xFF9B59B6)]).createShader(b),
          child: const Text('VMouse', style: TextStyle(
            fontSize: 14, fontWeight: FontWeight.w600, color: Colors.white, letterSpacing: 1)),
        ),
        const SizedBox(width: 12),
        TextButton(
          onPressed: () => Navigator.pop(context),
          style: TextButton.styleFrom(
            backgroundColor: const Color(0xFF111120),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
          ),
          child: Text('Disconnect', style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 11)),
        ),
      ]),
    );
  }

  Widget _buildTrackpad() {
    return GestureDetector(
      onScaleStart: (d) {
        _lastX = d.localFocalPoint.dx;
        _lastY = d.localFocalPoint.dy;
        _dragging = false;
        _touchStart = DateTime.now();
        _fingerCount = d.pointerCount;
        if (!_hintGone) setState(() => _hintGone = true);
      },
      onScaleUpdate: (d) {
        _fingerCount = d.pointerCount;
        final dx = (d.localFocalPoint.dx - _lastX) * _sensitivity;
        final dy = (d.localFocalPoint.dy - _lastY) * _sensitivity;
        _lastX = d.localFocalPoint.dx;
        _lastY = d.localFocalPoint.dy;

        if (_fingerCount >= 2) {
          if (dy.abs() > 1) {
            _send({'type': 'scroll', 'dy': (-dy / 6).round()});
          }
          return;
        }
        if (dx.abs() > 0.3 || dy.abs() > 0.3) {
          _dragging = true;
          _send({'type': 'move', 'dx': dx.round(), 'dy': dy.round()});
        }
      },
      onScaleEnd: (_) {
        if (!_dragging && _fingerCount < 2 &&
            DateTime.now().difference(_touchStart).inMilliseconds < 280) {
          _send({'type': 'click', 'button': 'left', 'clicks': 1});
          _setLog('Left click');
          _vibrate(25);
        }
        _dragging = false;
      },
      child: Container(
        color: const Color(0xFF0A0A12),
        child: Stack(children: [
          // Background glow
          Positioned.fill(child: Container(
            decoration: const BoxDecoration(
              gradient: RadialGradient(
                center: Alignment(0, 0.8),
                radius: 1.2,
                colors: [Color(0x1A6C5CE7), Colors.transparent],
              ),
            ),
          )),
          // Hint
          if (!_hintGone) Center(child: Column(
            mainAxisSize: MainAxisSize.min, children: [
              Icon(Icons.mouse, size: 48, color: Colors.white.withOpacity(0.05)),
              const SizedBox(height: 12),
              Text('Drag to move · Tap to click',
                style: TextStyle(fontSize: 12, color: Colors.white.withOpacity(0.2))),
              const SizedBox(height: 4),
              Text('Two fingers to scroll',
                style: TextStyle(fontSize: 12, color: Colors.white.withOpacity(0.2))),
            ],
          )),
          // Log chip
          Positioned(bottom: 12, left: 0, right: 0,
            child: Center(child: AnimatedOpacity(
              opacity: _log.isNotEmpty ? 1.0 : 0.0,
              duration: const Duration(milliseconds: 400),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.75),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: Colors.white.withOpacity(0.07)),
                ),
                child: Text(_log, style: TextStyle(
                  fontSize: 11, color: Colors.white.withOpacity(0.6),
                  fontFamily: 'monospace',
                )),
              ),
            ))),
        ]),
      ),
    );
  }
}
