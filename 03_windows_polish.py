"""VMouse script 03: Windows app polish. Sidebar icons, slim dark scrollbars, tray icon,
one version number, Windows-only dependency fix, line-ending file, unused files removed.
Run from the repo folder:  python 03_windows_polish.py
Aborts without changes if anything expected is missing."""
import base64, os, re, shutil, sys, zlib

def _payload(b64):
    return zlib.decompress(base64.b64decode(b64))

def read_text(path):
    raw = open(path, 'rb').read().decode('utf-8')
    nl = '\r\n' if '\r\n' in raw else '\n'
    return raw.replace('\r\n', '\n'), nl

def write_text(path, text, nl='\n'):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    open(path, 'wb').write(text.replace('\n', nl).encode('utf-8'))

def write_payload(path, b64):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    open(path, 'wb').write(_payload(b64))

def flex(t):
    return r'\s*'.join(re.escape(x) for x in re.findall(r'[(),]|[^\s(),]+', t))

class Patcher:
    def __init__(self, path):
        self.path = path
        self.text, self.nl = read_text(path)
        self.n = 0
    def sub(self, old, new, count=1, regex=False):
        pat = old if regex else flex(old)
        text, k = re.subn(pat, lambda m: new, self.text)
        if k != count:
            sys.exit(f'ABORTED, nothing changed. Expected {count} match(es) in {self.path} for {old[:70]!r}, found {k}')
        self.text = text
        self.n += k
    def has(self, s):
        return s in self.text
    def save(self):
        write_text(self.path, self.text, self.nl)

def need(path, what):
    if not os.path.exists(path):
        sys.exit(f'ABORTED: {path} not found. {what}')

def backup(path, tag):
    dest = os.path.join('..', f'{os.path.basename(path)}_before_{tag}')
    shutil.copy(path, dest)
    return dest

PAYLOAD = {
    'ui_kit.py': (
        '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'
    ),
    'tray.py': (
        'eNqVVMuO1DAQvOcrWj45woo4rwgX4DASy0NacUEoMklnxtrEDk4HGBD/TttJPM9dFl8S2+3qqnK7hRDvBzLO6g7G/UjYA3m9B1M7'
        'C9IiNiPQDmHgvbA+6PpebzEv4LXDEayjnbFbMC0YAhMXwNiRdNdhUwghMtMPzhODeNQNx2ZZ1mALmkjXO+mdIxWzVYOmnYJvk6FK'
        'D4MCMtRhKT7dumlEkd9kwIP8fv4JY4FeuKXl1rsePmzervubnhnHXfxZ40DwJn5Y9AHKI03ewjtn8VoeBoByBircgFYmxvl/And6'
        'JIb6LdgjQnEDwjrf6078yeJ+8IbV1Peywu9oqQwn8wPeCbEwIg4jBieLOJH5SQDfzRxj+EbXbArEL+d6bER+Crdy/LwQ/MLQ8S9F'
        'Paw1jEGP46wkEvpqbCPFi1fOtmY7eXzJmaM8BbppSvFM5Afd4879kFWwNqpWUBkuyHMHQqTHkZxnpafJL8xJPBoMsKbdn5mzGHSm'
        'uEzuXMIlyNnrZOP1vJ1pST6w17p6GqvW+fr8yh63ONl8gqZbQi+fq9WbI1/jm7JP8fbCwHCAlbrhiOETCuA6s/VtL9R6tBNX1/J8'
        'i1ueynTyeHXDTCX3KbSwdAMVa0UFdXrqqLzzE+bqkcMfObVQyYkldtYUe92Bx4anUqRE8fEv3UhFzvmVDhFs8pOtGgxtDRv5r76Q'
        '+mFxF/8kab9FKlck1qax59uK0kKx+bWQlpYSIrO/Rr6kpg=='
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
P = 'vmouse_server.py'
need(P, 'Run this inside the vmouse repo folder.')
p = Patcher(P)
if not p.has('_vm_attach_scroll'):
    sys.exit('ABORTED: apply fix_scrolling.py first (it is missing from vmouse_server.py).')
if p.has('ui_kit.VMScrollbar') or os.path.exists('ui_kit.py'):
    sys.exit('Already applied. Nothing to do.')
print('Backup:', backup(P, '03_polish'))

# 1. Helper modules
write_payload('ui_kit.py', PAYLOAD['ui_kit.py'])
write_payload('tray.py', PAYLOAD['tray.py'])

# 2. Modules
p.sub('STATUS_PORT = 8764', 'import ui_kit\nimport tray\n\nAPP_VERSION = "1.0.0"\nSTATUS_PORT = 8764')

# 3. One version number everywhere
p.sub('VMouse PC Server v4.0\nPowered by Bryt Ma Tech, Uganda' if False else 'VMouse PC Server v4.0', 'VMouse PC Server 1.0.0', count=2) if p.text.count('VMouse PC Server v4.0') == 2 else p.sub('VMouse PC Server v4.0', 'VMouse PC Server 1.0.0')
p.text = p.text.replace('print(f"  VMouse PC Server 1.0.0")', 'print(f"  VMouse {APP_VERSION}")')

# 4. Slim dark scrollbars (Windows ignores colors on its own scrollbar)
import re as _re
k = len(_re.findall(r'tk\.Scrollbar\(', p.text))
if k < 2:
    sys.exit('ABORTED: expected at least two scrollbars in the app.')
p.text = p.text.replace('tk.Scrollbar(', 'ui_kit.VMScrollbar(')
p.n += k

# 5. Sidebar icons drawn by the app (no font needed, same on Windows, Mac and Linux)
p.sub(r'(?s)def nav_button\(label, page_name, symbol\):.*?nav_buttons\[page_name\] = button',
'''nav_icons = {}

        def nav_button(label, page_name, symbol):
            icon_off = ImageTk.PhotoImage(ui_kit.nav_icon_image(page_name, "#8B8AA3"))
            icon_on = ImageTk.PhotoImage(ui_kit.nav_icon_image(page_name, "#A79EF5"))
            nav_icons[page_name] = (icon_off, icon_on)
            button = tk.Button(
                sidebar,
                text=f"   {label}",
                image=icon_off,
                compound="left",
                anchor="w",
                command=lambda: show_page(page_name),
                font=("Segoe UI", 10),
                bg=SIDEBAR,
                fg=MUTED,
                activebackground="#1F1F2B",
                activeforeground=TEXT,
                bd=0,
                padx=18,
                pady=11,
                cursor="hand2"
            )
            button.pack(
                fill="x",
                padx=12,
                pady=2
            )
            nav_buttons[page_name] = button''', regex=True)
p.sub('button.config(bg=SIDEBAR, fg=MUTED)', 'button.config(bg=SIDEBAR, fg=MUTED, image=nav_icons[key][0])')
p.sub('nav_buttons[name].config(bg="#1F1F2B", fg=TEXT)', 'nav_buttons[name].config(bg="#1F1F2B", fg=TEXT, image=nav_icons[name][1])')

# 6. Tray icon: minimizing sends VMouse to the tray when the pystray package is installed
p.sub('''show_page("connection")
        root.mainloop()''',
'''try:
            _vm_tray = tray.attach(root, icon_path, quit_app)
            if _vm_tray is not None:
                def _vm_to_tray(event=None):
                    try:
                        if event is not None and event.widget is root and root.state() == "iconic":
                            root.after(50, root.withdraw)
                    except Exception:
                        pass
                root.bind("<Unmap>", _vm_to_tray, add="+")
        except Exception:
            pass
        show_page("connection")
        root.mainloop()''')
p.save()
print(f'vmouse_server.py updated ({p.n} edits)')

# 7. Requirements, line endings, unused files
if os.path.exists('requirements.txt'):
    r = Patcher('requirements.txt')
    if 'sys_platform' not in r.text:
        r.text = r.text.replace('wmi>=1.5.1', 'wmi>=1.5.1; sys_platform == "win32"')
    if 'pystray' not in r.text:
        r.text = r.text.rstrip('\n') + '\npystray>=0.19.5\n'
    r.save()
    print('requirements.txt: wmi is Windows-only now, pystray added (tray icon)')
write_text('.gitattributes', '* text=auto\n*.png binary\n*.ico binary\n*.jpg binary\n*.keystore binary\n*.jks binary\n')
print('Added .gitattributes (stops the line-ending warnings)')
for name in ('github', 'googledrive', 'googlemaps', 'postgresql', 'stripe'):
    f = f'assets/{name}.png'
    if os.path.exists(f):
        os.remove(f); print('Removed unused', f)
print('\nDone. Now run: python vmouse_server.py')
