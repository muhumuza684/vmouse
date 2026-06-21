import 'dart:io';

/// WindowsInput — uses a persistent PowerShell process.
/// Commands execute instantly with no per-command startup delay.
class WindowsInput {
  static Process? _ps;
  static bool _ready = false;

  static Future<void> init() async {
    if (_ready) return;
    try {
      _ps = await Process.start('powershell', [
        '-NoProfile', '-NonInteractive', '-Command', '-'
      ]);
      _ready = true;
      // Drain stdout/stderr so the process doesn't block
      _ps!.stdout.listen((_) {});
      _ps!.stderr.listen((_) {});
    } catch (e) {
      _ready = false;
    }
  }

  static void _run(String script) {
    if (!_ready || _ps == null) return;
    try {
      _ps!.stdin.writeln(script);
    } catch (_) {
      _ready = false;
    }
  }

  static void moveRelative(int dx, int dy) {
    _run('''
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class M {
  [DllImport("user32.dll")] public static extern void mouse_event(int f,int x,int y,int d,int e);
}
"@
[M]::mouse_event(0x0001, $dx, $dy, 0, 0)
''');
  }

  static void click(String button, int clicks) {
    final down = button == 'right' ? 0x0008 : 0x0002;
    final up   = button == 'right' ? 0x0010 : 0x0004;
    for (int i = 0; i < clicks; i++) {
      _run('''
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class M${DateTime.now().millisecondsSinceEpoch} {
  [DllImport("user32.dll")] public static extern void mouse_event(int f,int x,int y,int d,int e);
}
"@ -ErrorAction SilentlyContinue
[System.Windows.Forms.SendKeys]::SendWait("")
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Cursor]::Position = [System.Windows.Forms.Cursor]::Position
''');
      _run('''
Add-Type -AssemblyName System.Windows.Forms
\$sig = @"
using System.Runtime.InteropServices;
public class NM {
  [DllImport("user32.dll")] public static extern void mouse_event(int f,int x,int y,int d,int e);
}
"@
Add-Type -TypeDefinition \$sig -ErrorAction SilentlyContinue
[NM]::mouse_event($down, 0, 0, 0, 0)
Start-Sleep -Milliseconds 50
[NM]::mouse_event($up, 0, 0, 0, 0)
''');
    }
  }

  static void scroll(int dy) {
    final amount = dy * 120;
    _run('''
\$sig = @"
using System.Runtime.InteropServices;
public class SC { [DllImport("user32.dll")] public static extern void mouse_event(int f,int x,int y,int d,int e); }
"@
Add-Type -TypeDefinition \$sig -ErrorAction SilentlyContinue
[SC]::mouse_event(0x0800, 0, 0, $amount, 0)
''');
  }

  static void hotkey(List<String> keys) {
    // Build SendKeys string
    final parts = <String>[];
    for (final k in keys) {
      switch (k.toLowerCase()) {
        case 'ctrl':  parts.add('^'); break;
        case 'alt':   parts.add('%'); break;
        case 'shift': parts.add('+'); break;
        case 'super': case 'win': parts.add('^{ESC}'); break;
        case 'tab':   parts.add('{TAB}'); break;
        case 'escape': case 'esc': parts.add('{ESC}'); break;
        case 'enter': parts.add('{ENTER}'); break;
        case 'delete': parts.add('{DELETE}'); break;
        case 'home':  parts.add('{HOME}'); break;
        case 'end':   parts.add('{END}'); break;
        case 'pageup': parts.add('{PGUP}'); break;
        case 'pagedown': parts.add('{PGDN}'); break;
        case 'left':  parts.add('{LEFT}'); break;
        case 'right': parts.add('{RIGHT}'); break;
        case 'up':    parts.add('{UP}'); break;
        case 'down':  parts.add('{DOWN}'); break;
        case 'f1': parts.add('{F1}'); break;
        case 'f2': parts.add('{F2}'); break;
        case 'f3': parts.add('{F3}'); break;
        case 'f4': parts.add('{F4}'); break;
        case 'f5': parts.add('{F5}'); break;
        case 'f6': parts.add('{F6}'); break;
        case 'f7': parts.add('{F7}'); break;
        case 'f8': parts.add('{F8}'); break;
        case 'f9': parts.add('{F9}'); break;
        case 'f10': parts.add('{F10}'); break;
        case 'f11': parts.add('{F11}'); break;
        case 'f12': parts.add('{F12}'); break;
        case '=': case 'equal': parts.add('{=}'); break;
        case '-': case 'minus': parts.add('-'); break;
        case 'l': parts.add('l'); break;
        case 'd': parts.add('d'); break;
        case 's': parts.add('s'); break;
        case 'c': parts.add('c'); break;
        case 'v': parts.add('v'); break;
        case 'z': parts.add('z'); break;
        case 'y': parts.add('y'); break;
        case 'a': parts.add('a'); break;
        case 'f': parts.add('f'); break;
        case 'p': parts.add('p'); break;
        case 'n': parts.add('n'); break;
        case 'w': parts.add('w'); break;
        case 't': parts.add('t'); break;
        case 'x': parts.add('x'); break;
        case 'b': parts.add('b'); break;
        case 'i': parts.add('i'); break;
        case 'u': parts.add('u'); break;
        default: parts.add(k);
      }
    }

    // Handle Win+key specially
    if (keys.any((k) => k == 'super' || k == 'win')) {
      final others = keys.where((k) => k != 'super' && k != 'win').toList();
      final keyStr = others.isNotEmpty ? others.join('') : '';
      _run('''
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.SendKeys]::SendWait("^{ESC}")
Start-Sleep -Milliseconds 200
if ("$keyStr" -ne "") {
  [System.Windows.Forms.SendKeys]::SendWait("$keyStr")
}
''');
      return;
    }

    // Wrap non-modifier keys in group
    final modifiers = parts.where((p) => p == '^' || p == '%' || p == '+').join();
    final mainKeys = parts.where((p) => p != '^' && p != '%' && p != '+').join();
    final sendStr = mainKeys.isNotEmpty ? '$modifiers($mainKeys)' : modifiers;

    _run('''
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.SendKeys]::SendWait("$sendStr")
''');
  }

  static void typeText(String text) {
    // Escape special SendKeys characters
    final escaped = text
        .replaceAll('+', '{+}')
        .replaceAll('^', '{^}')
        .replaceAll('%', '{%}')
        .replaceAll('~', '{~}')
        .replaceAll('(', '{(}')
        .replaceAll(')', '{)}')
        .replaceAll('[', '{[}')
        .replaceAll(']', '{]}')
        .replaceAll('{', '{{')
        .replaceAll('}', '}}');
    _run('''
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.SendKeys]::SendWait("$escaped")
''');
  }

  static void keypress(String key) {
    hotkey([key]);
  }

  static void dispose() {
    _ps?.stdin.close();
    _ps?.kill();
    _ps = null;
    _ready = false;
  }
}
