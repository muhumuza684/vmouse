import 'dart:ffi';
import 'package:win32/win32.dart';

// Uses only dart:ffi built-ins (malloc, sizeOf) — no ffi package calloc needed.

class WindowsInput {
  /// Move cursor by (dx, dy) relative to current position.
  static void moveMouse(int dx, int dy) {
    final p = malloc<POINT>();
    try {
      GetCursorPos(p);
      SetCursorPos(p.ref.x + dx, p.ref.y + dy);
    } finally {
      malloc.free(p);
    }
  }

  /// Send a left or right click.
  static void click({bool right = false}) {
    final input = malloc<INPUT>();
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
      malloc.free(input);
    }
  }

  /// Scroll vertically. Positive = up, negative = down.
  static void scroll(int dy) {
    final input = malloc<INPUT>();
    try {
      input.ref.type = INPUT_TYPE.INPUT_MOUSE;
      input.ref.Anonymous.mi.dwFlags = MOUSE_EVENT_FLAGS.MOUSEEVENTF_WHEEL;
      input.ref.Anonymous.mi.mouseData = dy * 120;
      SendInput(1, input, sizeOf<INPUT>());
    } finally {
      malloc.free(input);
    }
  }

  /// Press and release a virtual key.
  static void pressKey(int vk) {
    final down = malloc<INPUT>();
    final up = malloc<INPUT>();
    try {
      down.ref.type = INPUT_TYPE.INPUT_KEYBOARD;
      down.ref.Anonymous.ki.wVk = vk;
      down.ref.Anonymous.ki.dwFlags = 0;
      SendInput(1, down, sizeOf<INPUT>());

      up.ref.type = INPUT_TYPE.INPUT_KEYBOARD;
      up.ref.Anonymous.ki.wVk = vk;
      up.ref.Anonymous.ki.dwFlags = KEYBD_EVENT_FLAGS.KEYEVENTF_KEYUP;
      SendInput(1, up, sizeOf<INPUT>());
    } finally {
      malloc.free(down);
      malloc.free(up);
    }
  }

  /// Double-click left button.
  static void doubleClick() {
    click();
    click();
  }
}
