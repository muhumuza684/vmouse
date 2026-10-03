"""VMouse: minimize goes to the taskbar again (the tray icon stays, click it to restore the window).
Run from the repo folder:  python fix_minimize.py"""
import sys
P = 'vmouse_server.py'
s = open(P, encoding='utf-8').read()
a = 'root.bind("<Unmap>", _vm_to_tray, add="+")'
if a not in s:
    sys.exit('Nothing to change (already done, or script 03 was not applied).')
open(P, 'w', encoding='utf-8', newline='\n').write(s.replace(a, 'pass  # minimize stays on the taskbar'))
print('Done. Minimize now goes to the taskbar like any program. Run: python vmouse_server.py')
