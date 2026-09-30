import 'dart:io';

// Real Windows implementation — only compiled when dart.library.io is available
// AND we're actually on Windows (checked at runtime in pc_server_screen.dart).
class WindowsInput {
  static Process? _ps;
  static bool _ready = false;

  static Future<void> init() async {
    if (_ready) return;
    if (!Platform.isWindows) return;
    try {
      _ps = await Process.start('powershell', [
        '-NoProfile', '-NonInteractive', '-Command', '-'
      ]);
      _ready = true;
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
    _run(r'''
$sig = @"
using System.Runtime.InteropServices;
public class MV { [DllImport("user32.dll")] public static extern void mouse_event(int f,int x,int y,int d,int e); }
"@
Add-Type -TypeDefinition $sig -ErrorAction SilentlyContinue
[MV]::mouse_event(0x0001, ''' + '$dx, $dy' + r''', 0, 0)
'''.replaceAll(r'$dx', '$dx').replaceAll(r'$dy', '$dy'));
  }

  static void click(String button, int clicks) {
    final down = button == 'right' ? 0x0008 : 0x0002;
    final up   = button == 'right' ? 0x0010 : 0x0004;
    for (int i = 0; i < clicks; i++) {
      _run('''
\$sig = @"
using System.Runtime.InteropServices;
public class CL { [DllImport("user32.dll")] public static extern void mouse_event(int f,int x,int y,int d,int e); }
"@
Add-Type -TypeDefinition \$sig -ErrorAction SilentlyContinue
[CL]::mouse_event($down, 0, 0, 0, 0)
Start-Sleep -Milliseconds 40
[CL]::mouse_event($up, 0, 0, 0, 0)
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
    final parts = <String>[];
    for (final k in keys) {
      switch (k.toLowerCase()) {
        case 'ctrl':  parts.add('^'); break;
        case 'alt':   parts.add('%'); break;
        case 'shift': parts.add('+'); break;
        case 'win': case 'super': parts.add('^{ESC}'); break;
        case 'tab':   parts.add('{TAB}'); break;
        case 'esc': case 'escape': parts.add('{ESC}'); break;
        case 'enter': parts.add('{ENTER}'); break;
        case 'delete': parts.add('{DELETE}'); break;
        case 'backspace': parts.add('{BACKSPACE}'); break;
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
        default: parts.add(k.length == 1 ? k : '{$k}'); break;
      }
    }
    final modifiers = parts.where((p) => p == '^' || p == '%' || p == '+').join();
    final mainKeys = parts.where((p) => p != '^' && p != '%' && p != '+').join();
    final sendStr = mainKeys.isNotEmpty ? '$modifiers($mainKeys)' : modifiers;
    _run('''
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.SendKeys]::SendWait("$sendStr")
''');
  }

  static void typeText(String text) {
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

  static void keypress(String key) => hotkey([key]);

  static void dispose() {
    _ps?.stdin.close();
    _ps?.kill();
    _ps = null;
    _ready = false;
  }
}
