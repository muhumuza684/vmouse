import 'dart:ffi';
import 'package:ffi/ffi.dart' show calloc, CallocAllocator;
import 'package:win32/win32.dart';

class WindowsInput {
  /// Move cursor by (dx, dy) relative to current position.
  static void moveRelative(int dx, int dy) {
    final p = calloc.allocate<POINT>(sizeOf<POINT>());
    try {
      GetCursorPos(p);
      SetCursorPos(p.ref.x + dx, p.ref.y + dy);
    } finally {
      calloc.free(p);
    }
  }

  /// Click left or right button, optionally multiple times.
  static void click(String button, int clicks) {
    final bool right = button == 'right';
    for (int i = 0; i < clicks; i++) {
      final input = calloc.allocate<INPUT>(sizeOf<INPUT>());
      try {
        input.ref.type = INPUT_TYPE.INPUT_MOUSE;
        input.ref.Anonymous.mi.dwFlags = right
            ? MOUSE_EVENT_FLAGS.MOUSEEVENTF_RIGHTDOWN
            : MOUSE_EVENT_FLAGS.MOUSEEVENTF_LEFTDOWN;
        SendInput(1, input, sizeOf<INPUT>());
        input.ref.Anonymous.mi.dwFlags = right
            ? MOUSE_EVENT_FLAGS.MOUSEEVENTF_RIGHTUP
            : MOUSE_EVENT_FLAGS.MOUSEEVENTF_LEFTUP;
        SendInput(1, input, sizeOf<INPUT>());
      } finally {
        calloc.free(input);
      }
    }
  }

  /// Scroll vertically. Positive = up, negative = down.
  static void scroll(int dy) {
    final input = calloc.allocate<INPUT>(sizeOf<INPUT>());
    try {
      input.ref.type = INPUT_TYPE.INPUT_MOUSE;
      input.ref.Anonymous.mi.dwFlags = MOUSE_EVENT_FLAGS.MOUSEEVENTF_WHEEL;
      input.ref.Anonymous.mi.mouseData = dy * 120;
      SendInput(1, input, sizeOf<INPUT>());
    } finally {
      calloc.free(input);
    }
  }

  /// Press a combination of keys simultaneously (e.g. ['ctrl', 'c']).
  static void hotkey(List<String> keys) {
    final vks = keys.map(_keyNameToVk).whereType<int>().toList();
    // Press all keys down
    for (final vk in vks) {
      _keyEvent(vk, false);
    }
    // Release all keys in reverse
    for (final vk in vks.reversed) {
      _keyEvent(vk, true);
    }
  }

  /// Type a string of text character by character.
  static Future<void> typeText(String text) async {
    for (final ch in text.split('')) {
      final vk = ch.codeUnitAt(0);
      _keyEvent(vk, false);
      _keyEvent(vk, true);
      await Future.delayed(const Duration(milliseconds: 10));
    }
  }

  /// Press and release a named key.
  static void keypress(String key) {
    final vk = _keyNameToVk(key);
    if (vk != null) {
      _keyEvent(vk, false);
      _keyEvent(vk, true);
    }
  }

  // ── helpers ──────────────────────────────────────────────────────────────

  static void _keyEvent(int vk, bool keyUp) {
    final input = calloc.allocate<INPUT>(sizeOf<INPUT>());
    try {
      input.ref.type = INPUT_TYPE.INPUT_KEYBOARD;
      input.ref.Anonymous.ki.wVk = vk;
      input.ref.Anonymous.ki.dwFlags =
          keyUp ? KEYBD_EVENT_FLAGS.KEYEVENTF_KEYUP : 0;
      SendInput(1, input, sizeOf<INPUT>());
    } finally {
      calloc.free(input);
    }
  }

  static int? _keyNameToVk(String key) {
    const map = <String, int>{
      'ctrl': VIRTUAL_KEY.VK_CONTROL,
      'alt': VIRTUAL_KEY.VK_MENU,
      'shift': VIRTUAL_KEY.VK_SHIFT,
      'win': VIRTUAL_KEY.VK_LWIN,
      'enter': VIRTUAL_KEY.VK_RETURN,
      'backspace': VIRTUAL_KEY.VK_BACK,
      'tab': VIRTUAL_KEY.VK_TAB,
      'escape': VIRTUAL_KEY.VK_ESCAPE,
      'esc': VIRTUAL_KEY.VK_ESCAPE,
      'delete': VIRTUAL_KEY.VK_DELETE,
      'up': VIRTUAL_KEY.VK_UP,
      'down': VIRTUAL_KEY.VK_DOWN,
      'left': VIRTUAL_KEY.VK_LEFT,
      'right': VIRTUAL_KEY.VK_RIGHT,
      'home': VIRTUAL_KEY.VK_HOME,
      'end': VIRTUAL_KEY.VK_END,
      'pageup': VIRTUAL_KEY.VK_PRIOR,
      'pagedown': VIRTUAL_KEY.VK_NEXT,
      'f1': VIRTUAL_KEY.VK_F1,
      'f2': VIRTUAL_KEY.VK_F2,
      'f3': VIRTUAL_KEY.VK_F3,
      'f4': VIRTUAL_KEY.VK_F4,
      'f5': VIRTUAL_KEY.VK_F5,
      'f6': VIRTUAL_KEY.VK_F6,
      'f7': VIRTUAL_KEY.VK_F7,
      'f8': VIRTUAL_KEY.VK_F8,
      'f9': VIRTUAL_KEY.VK_F9,
      'f10': VIRTUAL_KEY.VK_F10,
      'f11': VIRTUAL_KEY.VK_F11,
      'f12': VIRTUAL_KEY.VK_F12,
    };
    final lower = key.toLowerCase();
    if (map.containsKey(lower)) return map[lower];
    if (lower.length == 1) return lower.codeUnitAt(0).toUpperCase();
    return null;
  }
}

extension on int {
  int toUpperCase() {
    if (this >= 97 && this <= 122) return this - 32; // a-z → A-Z
    return this;
  }
}
