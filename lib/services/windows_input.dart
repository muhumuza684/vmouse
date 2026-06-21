import 'package:flutter/services.dart';
import 'package:win32/win32.dart';
import 'package:ffi/ffi.dart';

/// Simulates real mouse and keyboard input on Windows using the Win32 API.
/// Uses SendInput — the modern, non-deprecated API — instead of the legacy
/// mouse_event/keybd_event functions, which newer win32 package releases
/// have removed entirely.
class WindowsInput {
  static const Map<String, int> _vk = {
    'ctrl': VK_CONTROL, 'control': VK_CONTROL,
    'alt': VK_MENU,
    'shift': VK_SHIFT,
    'super': VK_LWIN, 'win': VK_LWIN, 'windows': VK_LWIN,
    'tab': VK_TAB,
    'enter': VK_RETURN, 'return': VK_RETURN,
    'escape': VK_ESCAPE, 'esc': VK_ESCAPE,
    'space': VK_SPACE,
    'backspace': VK_BACK,
    'delete': VK_DELETE,
    'up': VK_UP, 'down': VK_DOWN, 'left': VK_LEFT, 'right': VK_RIGHT,
    'home': VK_HOME, 'end': VK_END,
    'pageup': VK_PRIOR, 'pagedown': VK_NEXT,
    'f1': VK_F1, 'f2': VK_F2, 'f3': VK_F3, 'f4': VK_F4, 'f5': VK_F5,
    'f6': VK_F6, 'f7': VK_F7, 'f8': VK_F8, 'f9': VK_F9, 'f10': VK_F10,
    'f11': VK_F11, 'f12': VK_F12,
    'volumeup': VK_VOLUME_UP,
    'volumedown': VK_VOLUME_DOWN,
    'volumemute': VK_VOLUME_MUTE,
    'playpause': VK_MEDIA_PLAY_PAUSE,
    'nexttrack': VK_MEDIA_NEXT_TRACK,
    'prevtrack': VK_MEDIA_PREV_TRACK,
  };

  static int _resolve(String key) {
    final k = key.toLowerCase();
    if (_vk.containsKey(k)) return _vk[k]!;
    if (key.length == 1) {
      // For letters/digits, Win32 virtual-key codes match uppercase ASCII.
      return key.toUpperCase().codeUnitAt(0);
    }
    return 0;
  }

  static void moveRelative(int dx, int dy) {
    final p = calloc<POINT>();
    try {
      GetCursorPos(p);
      SetCursorPos(p.ref.x + dx, p.ref.y + dy);
    } finally {
      calloc.free(p);
    }
  }

  static void _sendMouse(int flags, [int data = 0]) {
    final input = calloc<INPUT>();
    try {
      input.ref.type = INPUT_MOUSE;
      input.ref.mi.dwFlags = flags;
      input.ref.mi.mouseData = data;
      SendInput(1, input, sizeOf<INPUT>());
    } finally {
      calloc.free(input);
    }
  }

  static void click(String button, int clicks) {
    int down, up;
    switch (button) {
      case 'right':
        down = MOUSEEVENTF_RIGHTDOWN;
        up = MOUSEEVENTF_RIGHTUP;
        break;
      case 'middle':
        down = MOUSEEVENTF_MIDDLEDOWN;
        up = MOUSEEVENTF_MIDDLEUP;
        break;
      default:
        down = MOUSEEVENTF_LEFTDOWN;
        up = MOUSEEVENTF_LEFTUP;
    }
    for (var i = 0; i < clicks; i++) {
      _sendMouse(down);
      _sendMouse(up);
    }
  }

  static void scroll(int dy) {
    _sendMouse(MOUSEEVENTF_WHEEL, dy * 40);
  }

  static void _sendKey(int vk, {bool keyUp = false}) {
    final input = calloc<INPUT>();
    try {
      input.ref.type = INPUT_KEYBOARD;
      input.ref.ki.wVk = vk;
      input.ref.ki.dwFlags = keyUp ? KEYEVENTF_KEYUP : 0;
      SendInput(1, input, sizeOf<INPUT>());
    } finally {
      calloc.free(input);
    }
  }

  static void keypress(String key) {
    final vk = _resolve(key);
    if (vk == 0) return;
    _sendKey(vk);
    _sendKey(vk, keyUp: true);
  }

  static void hotkey(List<String> keys) {
    final vks = keys.map(_resolve).where((v) => v != 0).toList();
    for (final vk in vks) {
      _sendKey(vk);
    }
    for (final vk in vks.reversed) {
      _sendKey(vk, keyUp: true);
    }
  }

  /// Types arbitrary text (including non-English characters) by placing it
  /// on the clipboard and simulating Ctrl+V. This is far more reliable than
  /// sending one virtual key per character, and supports any language.
  static Future<void> typeText(String text) async {
    final previous = (await Clipboard.getData('text/plain'))?.text;
    await Clipboard.setData(ClipboardData(text: text));
    await Future.delayed(const Duration(milliseconds: 60));
    hotkey(['ctrl', 'v']);
    await Future.delayed(const Duration(milliseconds: 150));
    if (previous != null) {
      await Clipboard.setData(ClipboardData(text: previous));
    }
  }
}
