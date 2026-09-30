import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart';
import 'package:vibration/vibration.dart';
import '../services/connection_service.dart';
import 'qr_scan_screen.dart';

class TrackpadScreen extends StatefulWidget {
  /// 0 = Trackpad, 1 = Keyboard, 2 = Shortcuts. Defaults to Trackpad so
  /// every existing call site keeps working unchanged.
  final int initialTab;
  const TrackpadScreen({super.key, this.initialTab = 0});

  @override
  State<TrackpadScreen> createState() => _TrackpadScreenState();
}

class _TrackpadScreenState extends State<TrackpadScreen> {
  final _conn = ConnectionService();
  StreamSubscription<bool>? _statusSub;
  bool _connected = false;
  final TextEditingController _textCtrl = TextEditingController();

  // Tab
  late int _tab; // 0=trackpad, 1=keyboard, 2=shortcuts

  // ─── Gesture state (real-trackpad behavior) ────────────────────────────
  final Map<int, Offset> _pointers = {}; // pointer id -> last position
  DateTime? _gestureStartTime;
  bool _movedThisGesture = false;
  DateTime? _lastSingleTapTime;

  static const double _tapMoveThreshold = 6.0; // px — beyond this, it's a drag not a tap
  static const int _tapMaxDurationMs = 300;
  static const int _doubleTapWindowMs = 350;

  // ─── Touch ripple feedback (visual only — fires on every touch-down,
  // regardless of whether it turns into a tap, drag, or two-finger
  // gesture, same as how a real touchscreen gives instant feedback) ────────
  final List<_Ripple> _ripples = [];
  int _rippleIdCounter = 0;

  void _spawnRipple(Offset position) {
    final id = _rippleIdCounter++;
    setState(() => _ripples.add(_Ripple(position, id)));
    Future.delayed(const Duration(milliseconds: 320), () {
      if (mounted) setState(() => _ripples.removeWhere((r) => r.id == id));
    });
  }

  @override
  void initState() {
    super.initState();
    _tab = widget.initialTab;
    _connected = _conn.connected;
    _statusSub = _conn.connectionStatus.listen((isConnected) {
      if (mounted) setState(() => _connected = isConnected);
    });
  }

  void _send(Map<String, dynamic> data) => _conn.send(data);

  void _vibrate() async {
    if (await Vibration.hasVibrator() ?? false) {
      Vibration.vibrate(duration: 25);
    }
  }

  @override
  void dispose() {
    _statusSub?.cancel();
    _textCtrl.dispose();
    super.dispose();
  }

  // ─── Real trackpad gesture handling ────────────────────────────────────
  //
  // 1 finger drag   -> move cursor
  // 1 finger tap    -> left click (two quick taps -> double click)
  // 2 finger tap    -> right click
  // 2 finger drag   -> scroll
  //
  // Uses raw pointer events instead of GestureDetector because Flutter's
  // PanGestureRecognizer collapses multiple simultaneous touches into one
  // logical pan — there's no built-in way to tell "one finger" from "two"
  // through it. Tracking pointers directly gives us that distinction.

  void _onPointerDown(PointerDownEvent event) {
    _pointers[event.pointer] = event.localPosition;
    _spawnRipple(event.localPosition);
    if (_pointers.length == 1) {
      _gestureStartTime = DateTime.now();
      _movedThisGesture = false;
    }
  }

  void _onPointerMove(PointerMoveEvent event) {
    final prev = _pointers[event.pointer];
    _pointers[event.pointer] = event.localPosition;
    if (prev == null) return;

    final delta = event.localPosition - prev;
    if (delta.distance > 1.5) _movedThisGesture = true;

    // Only the lowest-numbered active pointer drives move/scroll output,
    // so a two-finger gesture doesn't get double-counted from both fingers
    // reporting movement independently.
    final primaryId = _pointers.keys.reduce((a, b) => a < b ? a : b);
    if (event.pointer != primaryId) return;

    if (_pointers.length >= 2) {
      _send({'type': 'scroll', 'dy': -(delta.dy * 2).round()});
    } else {
      _send({'type': 'move', 'dx': (delta.dx * 1.8).round(), 'dy': (delta.dy * 1.8).round()});
    }
  }

  void _onPointerUp(PointerUpEvent event) {
    final fingerCountForThisGesture = _pointers.length;
    final duration = DateTime.now().difference(_gestureStartTime ?? DateTime.now());
    _pointers.remove(event.pointer);

    if (_pointers.isNotEmpty) return; // wait for all fingers to lift

    final wasTap = !_movedThisGesture && duration.inMilliseconds < _tapMaxDurationMs;
    if (wasTap) {
      if (fingerCountForThisGesture == 1) {
        final now = DateTime.now();
        if (_lastSingleTapTime != null &&
            now.difference(_lastSingleTapTime!).inMilliseconds < _doubleTapWindowMs) {
          _send({'type': 'double_click'});
          _lastSingleTapTime = null;
        } else {
          _send({'type': 'click', 'button': 'left'});
          _lastSingleTapTime = now;
        }
        _vibrate();
      } else if (fingerCountForThisGesture == 2) {
        _send({'type': 'click', 'button': 'right'});
        _vibrate();
      }
    }
    _movedThisGesture = false;
  }

  void _onPointerCancel(PointerCancelEvent event) {
    _pointers.remove(event.pointer);
    _movedThisGesture = false;
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
              _conn.disconnect();
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

  // ─── Trackpad tab — pure gesture surface, no buttons ───────────────────────

  Widget _buildTrackpad() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 20),
      child: Listener(
        onPointerDown: _onPointerDown,
        onPointerMove: _onPointerMove,
        onPointerUp: _onPointerUp,
        onPointerCancel: _onPointerCancel,
        behavior: HitTestBehavior.opaque,
        child: ClipRRect(
          borderRadius: BorderRadius.circular(24),
          child: Container(
            width: double.infinity,
            decoration: BoxDecoration(
              color: const Color(0xFF0D0D1A),
              borderRadius: BorderRadius.circular(24),
              border: Border.all(color: const Color(0xFF1E1E32)),
            ),
            child: Stack(
              children: [
                Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.touch_app, color: const Color(0xFF6C5CE7).withOpacity(0.35), size: 40),
                      const SizedBox(height: 16),
                      const Text(
                        'Tap · Drag · Two fingers to right-click or scroll',
                        textAlign: TextAlign.center,
                        style: TextStyle(color: Color(0xFF444466), fontSize: 12.5),
                      ),
                    ],
                  ),
                ),
                ..._ripples.map(_buildRipple),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildRipple(_Ripple ripple) {
    const maxSize = 70.0;
    return Positioned(
      left: ripple.position.dx - maxSize / 2,
      top: ripple.position.dy - maxSize / 2,
      child: IgnorePointer(
        child: TweenAnimationBuilder<double>(
          tween: Tween(begin: 0.0, end: 1.0),
          duration: const Duration(milliseconds: 320),
          curve: Curves.easeOut,
          builder: (context, t, _) {
            return Opacity(
              opacity: (1 - t).clamp(0.0, 1.0),
              child: Container(
                width: maxSize * (0.4 + t * 0.6),
                height: maxSize * (0.4 + t * 0.6),
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: const Color(0xFF6C5CE7).withOpacity(0.22),
                  border: Border.all(color: const Color(0xFF6C5CE7).withOpacity(0.45), width: 1.5),
                ),
              ),
            );
          },
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

class _Ripple {
  final Offset position;
  final int id;
  _Ripple(this.position, this.id);
}
