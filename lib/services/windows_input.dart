import 'dart:io';

/// Controls mouse and keyboard on Windows by shelling out to PowerShell.
/// No win32/ffi dependencies — works with any Flutter Windows build.
class WindowsInput {
  static Future<void> _ps(String script) async {
    await Process.run(
      'powershell',
      ['-NoProfile', '-NonInteractive', '-Command', script],
      runInShell: true,
    );
  }

  /// Move cursor by (dx, dy) relative to current position.
  static void moveRelative(int dx, int dy) {
    // Use WScript.Shell SendKeys indirectly; for mouse we use the .NET type.
    _ps('''
Add-Type -AssemblyName System.Windows.Forms
\$p = [System.Windows.Forms.Cursor]::Position
[System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point(\$p.X + $dx, \$p.Y + $dy)
''');
  }

  /// Click left or right button, optionally multiple times.
  static void click(String button, int clicks) {
    final btn = button == 'right' ? 'Right' : 'Left';
    _ps('''
Add-Type @"
  using System; using System.Runtime.InteropServices;
  public class M {
    [DllImport("user32.dll")] public static extern void mouse_event(int f,int x,int y,int d,int e);
  }
"@
for (\$i=0; \$i -lt $clicks; \$i++) {
  [M]::mouse_event(${button == 'right' ? '0x8' : '0x2'},0,0,0,0)
  [M]::mouse_event(${button == 'right' ? '0x10' : '0x4'},0,0,0,0)
  Start-Sleep -Milliseconds 30
}
''');
  }

  /// Scroll vertically. Positive = up, negative = down.
  static void scroll(int dy) {
    final amount = dy * 120;
    _ps('''
Add-Type @"
  using System; using System.Runtime.InteropServices;
  public class M {
    [DllImport("user32.dll")] public static extern void mouse_event(int f,int x,int y,int d,int e);
  }
"@
[M]::mouse_event(0x800,0,0,$amount,0)
''');
  }

  /// Press a combination of keys simultaneously (e.g. ['ctrl', 'c']).
  static void hotkey(List<String> keys) {
    final combo = keys.map(_toSendKeys).join('');
    _ps('''
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.SendKeys]::SendWait("$combo")
''');
  }

  /// Type a string of text.
  static Future<void> typeText(String text) async {
    // Escape special SendKeys chars
    final escaped = text
        .replaceAll('+', '{+}')
        .replaceAll('^', '{^}')
        .replaceAll('%', '{%}')
        .replaceAll('~', '{~}')
        .replaceAll('(', '{(}')
        .replaceAll(')', '{)}')
        .replaceAll('[', '{[}')
        .replaceAll(']', '{]}')
        .replaceAll('{', '{{}}')
        .replaceAll('}', '{{}}}');
    await _ps('''
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.SendKeys]::SendWait("$escaped")
''');
  }

  /// Press and release a named key.
  static void keypress(String key) {
    final sk = _toSendKeys(key);
    _ps('''
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.SendKeys]::SendWait("$sk")
''');
  }

  static String _toSendKeys(String key) {
    const map = <String, String>{
      'ctrl': '^',
      'alt': '%',
      'shift': '+',
      'enter': '~',
      'backspace': '{BACKSPACE}',
      'tab': '{TAB}',
      'escape': '{ESC}',
      'esc': '{ESC}',
      'delete': '{DELETE}',
      'up': '{UP}',
      'down': '{DOWN}',
      'left': '{LEFT}',
      'right': '{RIGHT}',
      'home': '{HOME}',
      'end': '{END}',
      'pageup': '{PGUP}',
      'pagedown': '{PGDN}',
      'f1': '{F1}', 'f2': '{F2}', 'f3': '{F3}', 'f4': '{F4}',
      'f5': '{F5}', 'f6': '{F6}', 'f7': '{F7}', 'f8': '{F8}',
      'f9': '{F9}', 'f10': '{F10}', 'f11': '{F11}', 'f12': '{F12}',
      'win': '^{ESC}', // approximation
    };
    return map[key.toLowerCase()] ?? key;
  }
}
