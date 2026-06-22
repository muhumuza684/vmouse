import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:vibration/vibration.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'qr_scan_screen.dart';

class TrackpadScreen extends StatefulWidget {
  final String wsUrl;
  const TrackpadScreen({super.key, required this.wsUrl});

  @override
  State<TrackpadScreen> createState() => _TrackpadScreenState();
}

class _TrackpadScreenState extends State<TrackpadScreen>
    with TickerProviderStateMixin {
  WebSocketChannel? _channel;
  bool _connected = false;
  bool _showKeyboard = false;
  bool _scrollMode = false;
  final TextEditingController _textCtrl = TextEditingController();
  Timer? _heartbeatTimer;
  Timer? _pingTimeoutTimer;
  DateTime? _lastPong;

  // Gesture state
  Offset? _lastPos;
  int _pointerCount = 0;
  double _lastScrollY = 0;

  // Tab
  int _tab = 0; // 0=trackpad, 1=keyboard, 2=shortcuts

  @override
  void initState() {
    super.initState();
    _connect();
  }

  void _connect() {
    try {
      _channel = WebSocketChannel.connect(Uri.parse(widget.wsUrl));
      _channel!.stream.listen(
        (msg) {
          if (msg == 'pong') {
            _lastPong = DateTime.now();
            _pingTimeoutTimer?.cancel();
          }
        },
        onDone: _onDisconnected,
        onError: (_) => _onDisconnected(),
      );
      setState(() => _connected = true);
      _startHeartbeat();
    } catch (_) {
      _onDisconnected();
    }
  }

  void _startHeartbeat() {
    _heartbeatTimer?.cancel();
    _heartbeatTimer = Timer.periodic(const Duration(seconds: 5), (_) {
      _send({'type': 'ping'});
      _pingTimeoutTimer = Timer(const Duration(seconds: 10), () {
        if (mounted) setState(() => _connected = false);
      });
    });
  }

  void _onDisconnected() {
    _heartbeatTimer?.cancel();
    _pingTimeoutTimer?.cancel();
    if (mounted) setState(() => _connected = false);
  }

  void _send(Map<String, dynamic> data) {
    try {
      _channel?.sink.add(jsonEncode(data));
    } catch (_) {}
  }

  void _vibrate() async {
    if (await Vibration.hasVibrator() ?? false) {
      Vibration.vibrate(duration: 30);
    }
  }

  @override
  void dispose() {
    _heartbeatTimer?.cancel();
    _pingTimeoutTimer?.cancel();
    _channel?.sink.close();
    _textCtrl.dispose();
    super.dispose();
  }

  // ─── Trackpad gestures ────────────────────────────────────────────────────

  void _onPanStart(DragStartDetails d) {
    _lastPos = d.localPosition;
  }

  void _onPanUpdate(DragUpdateDetails d) {
    if (_lastPos == null) return;
    final dx = d.localPosition.dx - _lastPos!.dx;
    final dy = d.localPosition.dy - _lastPos!.dy;
    _lastPos = d.localPosition;

    if (_scrollMode) {
      _send({'type': 'scroll', 'dy': -(dy * 2).round()});
    } else {
      _send({'type': 'move', 'dx': (dx * 1.8).round(), 'dy': (dy * 1.8).round()});
    }
  }

  void _onPanEnd(DragEndDetails _) => _lastPos = null;

  void _leftClick() {
    _vibrate();
    _send({'type': 'click', 'button': 'left'});
  }

  void _rightClick() {
    _vibrate();
    _send({'type': 'click', 'button': 'right'});
  }

  void _doubleClick() {
    _vibrate();
    _send({'type': 'double_click'});
  }

  // ─── Keyboard ─────────────────────────────────────────────────────────────

  void _sendKey(String key) {
    _send({'type': 'key', 'key': key});
  }

  void _sendText(String text) {
    if (text.isEmpty) return;
    _send({'type': 'type', 'text': text});
    _textCtrl.clear();
  }

  // ─── UI ───────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(),
            _buildTabBar(),
            Expanded(child: _buildTabContent()),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(
        children: [
          const Icon(Icons.mouse, color: Color(0xFF6C5CE7), size: 22),
          const SizedBox(width: 8),
          const Text('VMouse', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 16)),
          const Spacer(),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: _connected ? const Color(0xFF0D2E1A) : const Color(0xFF2E0D0D),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(
                color: _connected ? const Color(0xFF00C853) : const Color(0xFFFF1744),
              ),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 6,
                  height: 6,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: _connected ? const Color(0xFF00C853) : const Color(0xFFFF1744),
                  ),
                ),
                const SizedBox(width: 5),
                Text(
                  _connected ? 'Connected' : 'PC Offline',
                  style: TextStyle(
                    color: _connected ? const Color(0xFF00C853) : const Color(0xFFFF1744),
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          IconButton(
            icon: const Icon(Icons.qr_code_scanner, color: Colors.white54, size: 20),
            onPressed: () {
              _channel?.sink.close();
              Navigator.of(context).pushReplacement(
                MaterialPageRoute(builder: (_) => const QRScanScreen()),
              );
            },
            tooltip: 'Reconnect',
          ),
        ],
      ),
    );
  }

  Widget _buildTabBar() {
    const tabs = ['Trackpad', 'Keyboard', 'Shortcuts'];
    const icons = [Icons.touch_app, Icons.keyboard, Icons.bolt];
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: const Color(0xFF111120),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF1E1E32)),
      ),
      child: Row(
        children: List.generate(3, (i) {
          final active = _tab == i;
          return Expanded(
            child: GestureDetector(
              onTap: () => setState(() => _tab = i),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 180),
                padding: const EdgeInsets.symmetric(vertical: 8),
                decoration: BoxDecoration(
                  color: active ? const Color(0xFF6C5CE7) : Colors.transparent,
                  borderRadius: BorderRadius.circular(9),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(icons[i], size: 14, color: active ? Colors.white : Colors.white38),
                    const SizedBox(width: 4),
                    Text(tabs[i],
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: active ? Colors.white : Colors.white38,
                        )),
                  ],
                ),
              ),
            ),
          );
        }),
      ),
    );
  }

  Widget _buildTabContent() {
    switch (_tab) {
      case 0:
        return _buildTrackpad();
      case 1:
        return _buildKeyboardTab();
      case 2:
        return _buildShortcuts();
      default:
        return const SizedBox();
    }
  }

  // ─── Trackpad tab ─────────────────────────────────────────────────────────

  Widget _buildTrackpad() {
    return Column(
      children: [
        const SizedBox(height: 12),
        // Scroll mode toggle
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Row(
            children: [
              const Text('Scroll mode', style: TextStyle(color: Colors.white54, fontSize: 12)),
              const SizedBox(width: 10),
              Switch(
                value: _scrollMode,
                onChanged: (v) => setState(() => _scrollMode = v),
                activeColor: const Color(0xFF6C5CE7),
              ),
            ],
          ),
        ),
        const SizedBox(height: 8),
        // Trackpad area
        Expanded(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: GestureDetector(
              onPanStart: _onPanStart,
              onPanUpdate: _onPanUpdate,
              onPanEnd: _onPanEnd,
              onDoubleTap: _doubleClick,
              child: Container(
                decoration: BoxDecoration(
                  color: const Color(0xFF0D0D1A),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: _scrollMode
                        ? const Color(0xFF6C5CE7).withOpacity(0.5)
                        : const Color(0xFF1E1E32),
                    width: _scrollMode ? 2 : 1,
                  ),
                ),
                child: Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        _scrollMode ? Icons.swap_vert : Icons.open_with,
                        color: const Color(0xFF6C5CE7).withOpacity(0.4),
                        size: 36,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        _scrollMode ? 'Swipe to scroll' : 'Swipe to move cursor',
                        style: const TextStyle(color: Color(0xFF444466), fontSize: 13),
                      ),
                      const SizedBox(height: 4),
                      const Text(
                        'Double-tap = double click',
                        style: TextStyle(color: Color(0xFF333355), fontSize: 11),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
        const SizedBox(height: 12),
        // Click buttons
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Row(
            children: [
              Expanded(
                flex: 2,
                child: _clickBtn('Left Click', Icons.mouse, _leftClick, const Color(0xFF6C5CE7)),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _clickBtn('Right', Icons.menu, _rightClick, const Color(0xFF2D2D4E)),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
      ],
    );
  }

  Widget _clickBtn(String label, IconData icon, VoidCallback onTap, Color color) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14),
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(14),
        ),
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

  // ─── Keyboard tab ─────────────────────────────────────────────────────────

  Widget _buildKeyboardTab() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          const SizedBox(height: 8),
          // Type text field
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
                    controller: _textCtrl,
                    style: const TextStyle(color: Colors.white, fontSize: 14),
                    decoration: const InputDecoration(
                      hintText: 'Type here to send text to PC…',
                      hintStyle: TextStyle(color: Color(0xFF444466), fontSize: 13),
                      border: InputBorder.none,
                    ),
                    onSubmitted: _sendText,
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.send, color: Color(0xFF6C5CE7), size: 20),
                  onPressed: () => _sendText(_textCtrl.text),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          // Key rows
          ...[
            ['Esc', 'Tab', 'Backspace', 'Enter', 'Delete'],
            ['F1', 'F2', 'F3', 'F4', 'F5'],
            ['Home', 'End', 'PgUp', 'PgDn', 'Ins'],
            ['←', '→', '↑', '↓', 'Space'],
          ].map((row) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                  children: row
                      .map((k) => Expanded(
                            child: Padding(
                              padding: const EdgeInsets.symmetric(horizontal: 3),
                              child: _keyBtn(k),
                            ),
                          ))
                      .toList(),
                ),
              )),
        ],
      ),
    );
  }

  Widget _keyBtn(String label) {
    final keyMap = {
      '←': 'left', '→': 'right', '↑': 'up', '↓': 'down',
      'Space': 'space', 'PgUp': 'page_up', 'PgDn': 'page_down',
      'Ins': 'insert', 'Del': 'delete',
    };
    return GestureDetector(
      onTap: () {
        _vibrate();
        _sendKey(keyMap[label] ?? label.toLowerCase());
      },
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: const Color(0xFF111120),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: const Color(0xFF1E1E32)),
        ),
        child: Center(
          child: Text(label, style: const TextStyle(color: Colors.white70, fontSize: 12, fontWeight: FontWeight.w600)),
        ),
      ),
    );
  }

  // ─── Shortcuts tab ─────────────────────────────────────────────────────────

  Widget _buildShortcuts() {
    final shortcuts = [
      ('Copy', 'ctrl+c', Icons.copy),
      ('Paste', 'ctrl+v', Icons.paste),
      ('Cut', 'ctrl+x', Icons.cut),
      ('Undo', 'ctrl+z', Icons.undo),
      ('Redo', 'ctrl+y', Icons.redo),
      ('Select All', 'ctrl+a', Icons.select_all),
      ('Save', 'ctrl+s', Icons.save),
      ('New Tab', 'ctrl+t', Icons.add),
      ('Close Tab', 'ctrl+w', Icons.close),
      ('Find', 'ctrl+f', Icons.search),
      ('Alt+F4', 'alt+f4', Icons.close_fullscreen),
      ('Print Screen', 'printscreen', Icons.screenshot),
      ('Task Mgr', 'ctrl+shift+esc', Icons.bar_chart),
      ('Show Desktop', 'win+d', Icons.desktop_windows),
    ];

    return Padding(
      padding: const EdgeInsets.all(16),
      child: GridView.builder(
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 2,
          childAspectRatio: 2.8,
          crossAxisSpacing: 8,
          mainAxisSpacing: 8,
        ),
        itemCount: shortcuts.length,
        itemBuilder: (_, i) {
          final (label, key, icon) = shortcuts[i];
          return GestureDetector(
            onTap: () {
              _vibrate();
              _send({'type': 'shortcut', 'keys': key});
            },
            child: Container(
              decoration: BoxDecoration(
                color: const Color(0xFF111120),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFF1E1E32)),
              ),
              padding: const EdgeInsets.symmetric(horizontal: 10),
              child: Row(
                children: [
                  Icon(icon, color: const Color(0xFF6C5CE7), size: 16),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(label, style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600)),
                        Text(key, style: const TextStyle(color: Color(0xFF555577), fontSize: 10)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
