import 'dart:ffi';
import 'dart:io';

// Raw user32.dll bindings — no win32 package needed at all.
// We define exactly what we need using dart:ffi directly.

// INPUT type constant
const int _INPUT_MOUSE = 0;
const int _INPUT_KEYBOARD = 1;

// Mouse event flags
const int _MOUSEEVENTF_MOVE = 0x0001;
const int _MOUSEEVENTF_LEFTDOWN = 0x0002;
const int _MOUSEEVENTF_LEFTUP = 0x0004;
const int _MOUSEEVENTF_RIGHTDOWN = 0x0008;
const int _MOUSEEVENTF_RIGHTUP = 0x0010;
const int _MOUSEEVENTF_WHEEL = 0x0800;
const int _MOUSEEVENTF_ABSOLUTE = 0x8000;

// Keyboard event flags
const int _KEYEVENTF_KEYUP = 0x0002;

// Key codes
const int _VK_CONTROL = 0x11;
const int _VK_MENU = 0x12; // Alt
const int _VK_SHIFT = 0x10;
const int _VK_LWIN = 0x5B;
const int _VK_RETURN = 0x0D;
const int _VK_BACK = 0x08;
const int _VK_TAB = 0x09;
const int _VK_ESCAPE = 0x1B;
const int _VK_DELETE = 0x2E;
const int _VK_UP = 0x26;
const int _VK_DOWN = 0x28;
const int _VK_LEFT = 0x25;
const int _VK_RIGHT = 0x27;
const int _VK_HOME = 0x24;
const int _VK_END = 0x23;
const int _VK_PRIOR = 0x21; // Page Up
const int _VK_NEXT = 0x22;  // Page Down
const int _VK_F1 = 0x70;

// Native structs using plain Uint8 arrays — avoids any win32 struct dependency.
// MOUSEINPUT: dx(4) dy(4) mouseData(4) dwFlags(4) time(4) dwExtraInfo(8) = 28 bytes
// KEYBDINPUT: wVk(2) wScan(2) dwFlags(4) time(4) dwExtraInfo(8) = 20 bytes
// INPUT: type(4) + padding(4) + union(28) = 36 bytes on x64

// We'll use mouse_event and keybd_event (simpler, always available in user32)
// These are the old API but work perfectly fine on all Windows versions.

typedef _MouseEventNative = Void Function(Uint32, Int32, Int32, Int32, IntPtr);
typedef _MouseEventDart = void Function(int, int, int, int, int);

typedef _KeybdEventNative = Void Function(Uint8, Uint8, Uint32, IntPtr);
typedef _KeybdEventDart = void Function(int, int, int, int);

typedef _GetCursorPosNative = Int32 Function(Pointer<Int32>);
typedef _GetCursorPosDart = int Function(Pointer<Int32>);

typedef _SetCursorPosNative = Int32 Function(Int32, Int32);
typedef _SetCursorPosDart = int Function(int, int);

class WindowsInput {
  static _MouseEventDart? _mouseEvent;
  static _KeybdEventDart? _keybdEvent;
  static _GetCursorPosDart? _getCursorPos;
  static _SetCursorPosDart? _setCursorPos;
  static bool _initialized = false;

  static void _init() {
    if (_initialized || !Platform.isWindows) return;
    try {
      final user32 = DynamicLibrary.open('user32.dll');
      _mouseEvent = user32
          .lookupFunction<_MouseEventNative, _MouseEventDart>('mouse_event');
      _keybdEvent = user32
          .lookupFunction<_KeybdEventNative, _KeybdEventDart>('keybd_event');
      _getCursorPos = user32
          .lookupFunction<_GetCursorPosNative, _GetCursorPosDart>('GetCursorPos');
      _setCursorPos = user32
          .lookupFunction<_SetCursorPosNative, _SetCursorPosDart>('SetCursorPos');
      _initialized = true;
    } catch (_) {}
  }

  static void moveRelative(int dx, int dy) {
    _init();
    if (!_initialized) return;
    // Use MOUSEEVENTF_MOVE with relative coords — simplest approach
    _mouseEvent!(_MOUSEEVENTF_MOVE, dx, dy, 0, 0);
  }

  static void click(String button, int clicks) {
    _init();
    if (!_initialized) return;
    final bool right = button == 'right';
    for (int i = 0; i < clicks; i++) {
      _mouseEvent!(right ? _MOUSEEVENTF_RIGHTDOWN : _MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0);
      _mouseEvent!(right ? _MOUSEEVENTF_RIGHTUP : _MOUSEEVENTF_LEFTUP, 0, 0, 0, 0);
    }
  }

  static void scroll(int dy) {
    _init();
    if (!_initialized) return;
    _mouseEvent!(_MOUSEEVENTF_WHEEL, 0, 0, dy * 120, 0);
  }

  static void hotkey(List<String> keys) {
    _init();
    if (!_initialized) return;
    final vks = keys.map(_keyNameToVk).whereType<int>().toList();
    for (final vk in vks) {
      _keybdEvent!(vk, 0, 0, 0);
    }
    for (final vk in vks.reversed) {
      _keybdEvent!(vk, 0, _KEYEVENTF_KEYUP, 0);
    }
  }

  static Future<void> typeText(String text) async {
    _init();
    if (!_initialized) return;
    for (final ch in text.split('')) {
      final vk = ch.toUpperCase().codeUnitAt(0);
      _keybdEvent!(vk, 0, 0, 0);
      _keybdEvent!(vk, 0, _KEYEVENTF_KEYUP, 0);
      await Future.delayed(const Duration(milliseconds: 10));
    }
  }

  static void keypress(String key) {
    _init();
    if (!_initialized) return;
    final vk = _keyNameToVk(key);
    if (vk != null) {
      _keybdEvent!(vk, 0, 0, 0);
      _keybdEvent!(vk, 0, _KEYEVENTF_KEYUP, 0);
    }
  }

  static int? _keyNameToVk(String key) {
    const map = <String, int>{
      'ctrl': _VK_CONTROL,
      'alt': _VK_MENU,
      'shift': _VK_SHIFT,
      'win': _VK_LWIN,
      'enter': _VK_RETURN,
      'backspace': _VK_BACK,
      'tab': _VK_TAB,
      'escape': _VK_ESCAPE,
      'esc': _VK_ESCAPE,
      'delete': _VK_DELETE,
      'up': _VK_UP,
      'down': _VK_DOWN,
      'left': _VK_LEFT,
      'right': _VK_RIGHT,
      'home': _VK_HOME,
      'end': _VK_END,
      'pageup': _VK_PRIOR,
      'pagedown': _VK_NEXT,
    };
    final lower = key.toLowerCase();
    if (map.containsKey(lower)) return map[lower];
    // F1-F12
    if (lower.startsWith('f')) {
      final n = int.tryParse(lower.substring(1));
      if (n != null && n >= 1 && n <= 12) return _VK_F1 + n - 1;
    }
    // Single character
    if (lower.length == 1) return lower.toUpperCase().codeUnitAt(0);
    return null;
  }
}
