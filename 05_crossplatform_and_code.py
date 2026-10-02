"""VMouse script 05: Windows, Mac and Linux support, one file per page, and tests.
Run from the repo folder:  python 05_crossplatform_and_code.py   (after scripts 01 to 04)
Moves each window page out of the 2,300-line function into ui/page_*.py, makes power and app-opening
commands work on Mac and Linux, and adds an automatic test suite.
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
    'platform_utils.py': (
        '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'
        'gPmCsakteTdoE6S9/wHRk2k4'
    ),
    'system_handler.py': (
        'eNqtVt9v2zYQftdfcdCGxQYUb3voS7YU8BwPLdbEQeJ0GNrCo6VzzFoiBZJKYmT+3/eRlBw7KZoGmx/IE3l3/O630zRNLtfWcUW5'
        'Vs7okipdNCXTQht6f6oby3Q+Isvmhs0geSNUUbKlWt+yIV2zEU5qZQnnJMiwdUbmjgtIONILKqS4Vto6meOBqgKbHSTJ5Xh0dfF2'
        '+hedTabjo2SiyjU0kChLfXtYShtEDYviUPurTpJyMJlGDWio1m4p1TUpDV5FbskU5KSF3Gf2ELLEg7JLLkvKl0Iqzw/CCNwaQDYM'
        '3gUsLAY0hnn+IaUgC4uoaqBNlFZTLawND9RCmqiD81UiFd1U3j+z1jn1muYMtzFJF5GyyJeQBKbo1EGSwt+yqrVxZJt5bXTO1iYL'
        'oyty69orb29P4MXMm5l0/HUpHLRXs8bJ0iZJUvCC+I7zxgFCiOEshKUnggVHhFj06fB10PUBH0Hfp6OE8AOQcZRtYxmFLKSWjSv0'
        'rcpCNIUBDFsy1xmVOl/59Vo3OFzKORslHGfe2JzLgTfO65aLVluIDvy0D31wPvlzfDEbjqZvJ2eXEY7/GXaNUXSf4lXX2PSIUjZG'
        'mzSjtIKbxDXjbJFeqZUCPurMvI/EJt0EVYw0XtPx40eDlbM2k1oX9Tu4UQZxOtOKvw1R1ICjSOxhTKc+5q0PQHk3iBshSzFHZYV0'
        'xSmw1PC/aXHnVZFRqwPwA6Rwgf0B0kPWDM5RfqoXxEKSH09Ng2BYRK9xxzuMJ+P3Z1fv3oUr4P/CVf9rJtsm97zPGd1SbRDucq4d'
        'jcPmvSAs/Q+ORRL3uL9B8l8Ofx/PRpPT0+HZyeXTaFux4C7YttdPku9o1DURtxSOFKNkfS/JCJTySWB1xQg/iSIwoSU6Tfvv4BHf'
        'BWdvhhcns9/eTUZ/jE/w+H0sqYJLbwB6omVPeDzCecoUYa0KaSIRVr72m839qjgwhiwN0fRfiK3fbisJnviGE3a1kvG62wtpVzUK'
        '1dPzvOBCBlI49OJ50CPrJceXGyVCJLsqj0DmWrvuBdsUOnA0QXSJ1hWJlrsIn9VqEfTkjQkYbq+jAXNhl1F/MAddGrHMks2jfpWj'
        'u+pqW47t/mzLumiQSV+YKdnu5EHU9mbJbl/yldjKEAbczufAy9e9/kv7UTquarcdUV0tt08cP9beVfrMx8vu3teldO09fAgPVUG8'
        'Y/3w06dBGbp739vxoIJLTOgHA7eyaLt7afpVu+a+tXPxuNMe3HfqNgddH8PIr6TzftahgrjSmCGdwTG+vn43TxC1w2Cvop6i2h7E'
        'ZHwKcZ/hObjtf4OQDcDc4Qx5QcN4ihFykNHB4LOWqmcxa7no7aHs9zc7724tE2rdw4CHTZ1a/6cpnvTSH7w3//HLL3752y/f9/z6'
        '2i+/+uVjqKiPJu33Xx6ftO1o2z83PxqUvuG9sbMNVxuQvWGComlKhzTbmQjoEL1tVe3OlVzUwMUzDBeMrfbQ8d2WlGifuPj51bdO'
        'k6gJhxHHIE6urCuz3XOceI/vH4TU9xN7b+bs2DKNkMZ3NdxSvLiyO/96y5DugPqfh9vTUfYvlGG0Tg=='
    ),
    'tests/test_pairing.py': (
        'eNqlV21v2zYQ/u5fwWlfZNRTZKdxnQDakKZOFzRNjDjDOgwDQUsnS7HeQNJxg2H/fXeUbNF2krlrjEAyeS/P3T13pNO8KqVmD6os'
        'Omn9rlTWWb9XIpVpMe90OhHETIPSXJcLKHiqeChBaIi4KCK+gEq7Oq94JXTSPesw/ItTqTQL1ja8Sf2c6lJCK2tExVykxYGiSgEC'
        'y6BwjQPP4OmynwPWH9oS1i4LgtpF/dWORoICzXOxAMUFL2BVx7cbiyIkhwEsswgFjULjzgJVLxunbpf9EJC0vf+6/TYa27wVzUya'
        '4sRpBlQhCVUmQoh2o9l8Z0fMWbskCjhdbyVTDVzDV+06RVkzw9lL/SE41zWx8K1gxtUq1WFC8JR43Mf2DZneyqnIsnJFDliq2L1c'
        'QmvNoxJv9t1LkSnofkPWt0wbbTum+VJIbIIwxBbAlKfzRJuWkPAAIa6sZFnMd6M0SvtRfqTl/0juFnJjxwsTCBeu0/cG3rH31uk1'
        'yxZJukQal9LSY065cA4x4hjkTq1qwsa1mYjqDjnIxE1ZwPfoO6943yvBLCvDBXZxrEES9evpFIs0W2LDcZ1gZ0gIy0eQarceIeli'
        'Pf52tHPG+r7ve/4/31upHivKVZCJfBaJs9rFn2j/rzryuJSMMxx7UhRz2Jj6fP6FX55fXf92N5424DYw1gk69czHqTPySiZbwRcY'
        'sUksgYPXTI088zmIXIz9yErMt2RVggxQTGBL0zARcYw9AVGbc5MQ9qbN7/vr24tPfDq+uL35MGVvWP//B2fT3WJL44kvZcYToTgg'
        'IZ50QkuImRvIeBJApNymAChpMcDSR66eDrz+cOQhZ32qB7qnh5iFET51pgJCsZVW1EOsQmqahInrJFpXZ0dHtqWzkT/yj35xWqZU'
        'KE9kcZ1F0PiIq6Bx45CfvmlZpYLRu+FJ/U6vQ8di0Wbe1cYQyVZiZPqIPcNFFGHD4AFv8tyo74xKmt+NfJsE3zvB4uPwe0HM90xr'
        'vyrzboDxo1x/m4vEnmcV1rysbb4oRnaPB4iwv00GvCXACgc8D8s8p7FdiBwaTnC6Aq3jD3N7CuyqIVXaUpVNqdbCv0+Jz9jQfHJ7'
        'd99j1vrk+vzqZmf51/v7yTNLU7O2X0ylpUsuu+QTUdrRhSiQxmlIVY3REEhMSEH3HTyCYW8KxrLM2W0FxXR6zZobYCifKl2a7QU8'
        'YQrqBW/yCZ6aoHHdm0MBktzgF7cRuf9jMuZ30/MeG/hvR7UsIWqNfDnxT912A61orpYzOjjdrndxg5LOY14uFfxE8TitJB3pGH4q'
        'Ml4s8xlIt2/byXWaE5EfODLiPcQ0l/0XBc7pyHCPh74tQh5SpZa4s49tR65azihu/Lc30nlBS9iKKhGDk2HD6AryNgPREktglWmd'
        'u8ur67HJ32T8uWfsdb0ID68ImnyZ61vA7Juc8YrWnY2AfZvDjVqzKSyOviRLZ881Nxmy+eIajtBMbZQ8DKjv4g8FD+EZ+Hgs8w/j'
        'O/NuXHW9BL5G6RzLhoj/Bf9uBt0='
    ),
    'tests/test_web_static.py': (
        'eNplU02L2zAQvftXCMGCTY3spAuFZVN6KfTYw96WRcjWOBZrW640bhJK/3tHttLYWdsQaT7ee/MR04/WIfO2fgdMzHKbXNeZSoBz'
        '1t3ZHPyawGNyNY8XXF9PUEmPCk2dJImGhjUOQAZXmj0ljB7PDpFNLD9ptthFZQadpny3/yJKenc8Z2W2OGdsyhNHwJA1qB7S7HX3'
        'FlPrznqIQA5wcsOcQhq+LQJFY85kDjFBlTcIKfajHBW2Udh4UkRxNbKCcbLwq0v079q4SJGGWAogwXAWLfYdz8TJEahEOGPKn9vd'
        '1xa6zj4XdOLbLD9VFL7BW7N6qKkEgWe8A9WWDZZGBe438E1fVk1eGhJCHDlu4xCzTbaIY9CRz6lL9MVAp1nDg++pKP73/+lPiPnL'
        'V5DCtxNqexo2RAu2k9cpLJOnUaW0NLG76C7LITwnQ6VuF0rQ1Y4whJScoenBTnj4nDHlmbtlrgZMtFTZ5HM6OVA6SoJzDeN2hcWP'
        'l5ef38MpoMENLSKBqK2GnFWcR+1hZeRclZfYUm/VEdKwNNcljsyV1Rdqcyg1eNknxos4GuUpH2MkOxzYviyZGjSxzJvBmRnm/DWl'
        'JTInG9MRL8VKdIoa61UnlQPpoJk86LWQhmqaF4fAUl6sdicnKULcWx72QN/HuId9c2ejVWvNcOTZrV2xpFW189/ntXwL9T2Wj/ls'
        'WBc0WElrDjVad5Gd8UiQa/0fIamIqaIm3lCTf15+caY='
    ),
    'tests/test_platform_and_system.py': (
        'eNq1VU1P3DAQve+vsKyqSiQ+yhVEJYRaiUOhKkgcEDKuPdu469iWx2ZZqT++4yQbslsKtFVzWK09b/zem8w4pg0+JhasTHMfW5GT'
        'scgkspBnpo/hChO0opFOW4glhs1sNtMwZwkwCbiHuBLBLyEKqZLxjrAopFC+bSlJ+CgMCg3KyghaZIc5lJNBV/XhjNFD1KxPZcYR'
        '9d7ni+sPX8TJ6dXZxflljykPuBRX7Lgger6BouqT6xEoEYGk93iD7Nw7YERSGTQOk3QKqi548+52h2GKNaNj2C/RgyFaTw1nt3B+'
        '6TYtk8MI30FNXA0isNmDB1A5gRhK2SVWHB6C9Rp4fcOJNGXkt+z4mHGI0Uc+ZVwap/0SxQJWwskWsGq9o0WQSTUD22RnD4HOS7EK'
        'eYfxs0txfXbOd9hVzFC/iP10ckrYj9LiAB5sUM2lliEVEViR5BwgEpJrflsX3TecZA4bzyWqFG2BqTFvsjN13UolMgKOjURtIrCh'
        'zqFi/l0JJrZersFjvV7vpFe6NvNM7mOtfk3Vm3X4ar1a0OCUEqx7b0DTWHnhfBIxu+kwqVaXSap412rYgO2Expbtxjnb70jAsofy'
        'B7P2zGKnOUfLmpTC4f5+Fwur1NBQ7ip2UJbEJNc668PtaZs0usqYfDuOJ8nZbvLBFJ1Kwalb1UjjjPvWT9ScGkA/6QxU41lj2Fu2'
        'bLxsTdG33vtBbzfCZOfoCdB7Njf2EXRn9N24eFMZXf83i9CGtBozf3tbbDFwAr3irpDW0jvX49BQZ+Caw+dEt+czFJ35+9ZT1flG'
        '61PmFjNmpQCRdxcnH3LKq+mg9BNy2uxjH8AJGcJwUaLwWv/DdfZHszwB+8UOE/1HZK2o4kpadcTG+dj0viifkO6E2U8yOlzE'
    ),
    'tests/conftest.py': (
        'eNrLzC3ILypRyC/myoSwiiuLubiAhF5BYkmGXmZecWpRiYaBDlAFRCQlsygvMTdVAxc/MakYRGvEx6dl5qTGx2sCARcAciEkHQ=='
    ),
    'tests/test_server_protocol.py': (
        'eNqtVm1v2zYQ/u5fwfET1bmMUyRtEUzAgsRbg7lxELsFhiIgaOlsc5ZEjaT8giL/fUeKfssL0A1zEFvkHe/lubuHopSOnDTOEjcH'
        'YkAWxIJZgiGyykk2h2xhSS2VUdWMAG457X84GS1UXUNOVnMwQCpNcmXrQm6IskQupSrkpABOKe2ostbGEWk3Vab0dvmX1dX2Wdvt'
        'k503ThW7lc4W4HYruxc0k9roDOz+4Gb36FQJnanRJcbt5oWakCi4w2Vnq1VvHFjX6dwPh2OSBhkTYqoKECLhBqwulsASXksDlYs/'
        'nfZUKc0Cz7QL7lfcIhxqyjoEP5V2hLWZ8NVcZXNG18vp5K1pKpoQbTBfDtVSGV3xGThGr29Gd4PLP2mSdH0JEJmUVgA5IrmDlW1N'
        'JDTpdDo5TMlKKid8Msx/dUPiunHpWS+5CIH4eqVhm/svlpCft0pBjsEVcCT/xZ9pDwcF5eaxCrz9QR1pid2r+I/lFlw0zHr8PDmS'
        'qikqZLqqIHMC1ozR03cfeA//TmmX+NCThKQp6R0b9R8DrjEVGZsGdrIQri0AanR11rqKer/JwgKC82uszFStcR+YzXQNKS113hSA'
        '8Hnw2i5nrqyFbxMxlZnTZhORy6WTHronUl4uHJQ1o4XMaRIxXqJirjLH9mXtksHw6nJweXd3fTm+TK0zzFvE8n79PPwy6otP/cvr'
        'QX80SulptJOVvlbfsI85rCFrnJ+fLvFHQ4ueELosdWNBtJHzekOTh84W4Ne6zU+x78dXW24Peoxgf7pL6FtJH7BpUBTU/NChzn78'
        '+B0iWzGUd0m2ylMfatdjkuK/jz73DXmgf93/evtlMAgiMOYl0bMuOGo1T1aighXCYK3CSfGwV7IE8lNKaOVwiIIBZzb71KRF0NzB'
        'wHz88P49VoNGrstVi1KwTvetphdQYb6eq3ihZW5ZqKMvxtfPvhjUP0Z65F6Neu6QuXCwxllJvtFggz7sbG4UFHlrOexNVSWL4iDW'
        'o8Bjebcppm2KzwfFY8gXqijY8ewBDsRz7S1nqhn6fiZFZ95SPWPBaq2wtq0qH938/sfNYLD3AesMakf64QercezrpajCni8E29LV'
        '6fmW0FxhWWzI0GYWPY4GV7oKaPrl3f1wPLwaDsR4MBJXg5v+7TiODw93lZhr61qoIhu0Qiyymm4EMgBEw1f9+7G4Hd72Dwkkw0DC'
        'PUVCOLJYsMaoLhbJWCTYN28WqxhfhHAFk5YXbaftM382sOZesuW+1lSw4Tl0dUCi0gOCO8ijVc5Cu+VNWVsWHCd79GKcBw25O2og'
        'W2LHRShxflmmjY7hxnPxDuY76RZ4ZEth1GzuRIYQCWWFzHxJIWftiEQ7cZD8+YAOxSxOTnZ8fuHnCnnjO3WbGugFobJxc08k7Rhc'
        'RNp9DJPhVR5CT3stoRf0NR/PnJz/iJOuL3Qamuo1fwfpZ7oskS2t8OXDvhRxrAXe/MLAFKf9CRgG6mKD7fTjaJR6CT7QfI2rc/+w'
        '8Q+PscLbzFu76ZMM8RLC6zr359uXhJ3AwN+NMih6PEyolrNQyRBzLiaYktWNycImst1xMrGhG1PgGxNHatbmhX3vyb82HUR7LOG4'
        'DFcCnTtXH6PR+9g7ofvXlPOEI9+6xvpU3/V6nd0bR7y+jVRI8uwwJP5pPL7r+6cwQ7i3H6J/F8izy/QwsMP80AdfyqIBngX2SMlZ'
        '7+wQ5xVeqrMwN1bg3SomhZ/7XBTSPsF4iu9+iqiKGFnNgJ0nz26o/z5YUzqR+Xf1SF+crdg6//sMx0ZsPcXEaecf5VPPhw=='
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
import ast, builtins, textwrap
P = 'vmouse_server.py'
need(P, 'Run this inside the vmouse repo folder.')
need('pairing.py', 'Run scripts 01 to 04 first.')
p = Patcher(P)
if p.has('platform_utils'):
    sys.exit('Already applied. Nothing to do.')
for marker in ('_vm_attach_scroll', 'PAIRING_STORE', 'ui_kit.VMScrollbar'):
    if not p.has(marker):
        sys.exit(f'ABORTED: run scripts 01 to 04 first ({marker} is missing from vmouse_server.py).')
print('Backup:', backup(P, '05_crossplatform'))

# ── Part A: Windows, Mac and Linux ───────────────────────────────────────────
write_payload('platform_utils.py', PAYLOAD['platform_utils.py'])
backup('system_handler.py', '05_crossplatform')
write_payload('system_handler.py', PAYLOAD['system_handler.py'])
p.sub('STATUS_PORT = 8764', 'import platform_utils\nSTATUS_PORT = 8764')
p.sub('''pyautogui.press("win"); time.sleep(0.6)
            pyautogui.typewrite(app, interval=0.05); time.sleep(0.5)
            pyautogui.press("enter")
            log.info(f"Open app: {app}"); stats["keystrokes"] += 1
            return {"type": "echo", "text": f"Opening {app}...", "status": "✓ Done"}''',
'''ok, why = platform_utils.open_app(app, pyautogui)
            log.info(f"Open app: {app} ({'ok' if ok else why})"); stats["keystrokes"] += 1
            return {"type": "echo", "text": why, "status": "✓ Done" if ok else "✗ Failed"}''')
p.sub('parts = [k.strip().replace("super", "win").replace("win+", "win") for k in raw.split("+")]',
      'parts = platform_utils.adapt_keys(raw.split("+"))')
p.sub('keys = [k.replace("super", "win") for k in data.get("keys", [])]',
      'keys = platform_utils.adapt_keys(data.get("keys", []))')
p.sub('k = key.replace("super", "win")', 'k = "+".join(platform_utils.adapt_keys(key.split("+")))')
p.sub('net_hint = pairing.network_hint(ip)', 'net_hint = pairing.network_hint(ip) or platform_utils.startup_notice() or ""')
p.save()
print(f'Part A: Mac and Linux support added ({p.n} edits)')

# ── Part B: split the window code into one file per page ─────────────────────
text, nl = read_text(P)
tree = ast.parse(text)
lines = text.split('\n')
fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'show_qr_popup')

def container_of(node):
    body = getattr(node, 'body', None)
    if isinstance(body, list) and any(isinstance(s, ast.FunctionDef) and s.name == 'connection_page' for s in body):
        return body
    for child in ast.iter_child_nodes(node):
        found = container_of(child)
        if found:
            return found
box = container_of(fn)
if not box:
    sys.exit('ABORTED: could not find the page functions. Nothing was split.')
NAMES = ['connection', 'activity', 'system', 'products', 'about', 'support']
funcs = {s.name: s for s in box if isinstance(s, ast.FunctionDef)}
if any(f'{n}_page' not in funcs for n in NAMES):
    sys.exit('ABORTED: a page function is missing. Nothing was split.')

def stores(node):
    out = set()
    for x in ast.walk(node):
        if isinstance(x, (ast.FunctionDef, ast.ClassDef)): out.add(x.name)
        if isinstance(x, ast.Name) and isinstance(x.ctx, (ast.Store, ast.Del)): out.add(x.id)
        if isinstance(x, ast.arg): out.add(x.arg)
        if isinstance(x, (ast.Import, ast.ImportFrom)):
            for a in x.names: out.add((a.asname or a.name).split('.')[0])
        if isinstance(x, ast.ExceptHandler) and x.name: out.add(x.name)
    return out

# every import line in the app, by the name it creates (module level and inside show_qr_popup)
imports = {}
def collect(node):
    for x in ast.walk(node):
        if isinstance(x, (ast.Import, ast.ImportFrom)):
            line = ast.get_source_segment(text, x)
            if line and '\n' not in line:
                for a in x.names:
                    imports.setdefault((a.asname or a.name).split('.')[0], line)
collect(tree)
builtin_names = set(dir(builtins))
module_defs = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}

needs = {}
ctx_names = set()
for n in NAMES:
    node = funcs[f'{n}_page']
    used = {x.id for x in ast.walk(node) if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load)}
    free = sorted((used - stores(node)) - builtin_names)
    mod_imports = [imports[f] for f in free if f in imports]
    shared = [f for f in free if f not in imports and f != '__file__' and f != 'show_page' and f != f'{n}_page']
    needs[n] = (mod_imports, shared, 'show_page' in free, '__file__' in free)
    ctx_names.update(shared)

os.makedirs('ui', exist_ok=True)
write_text('ui/__init__.py', '"""VMouse PC app pages. Each page lives in its own file: edit them here."""\n', nl)
for n in NAMES:
    node = funcs[f'{n}_page']
    body = '\n'.join(lines[node.lineno - 1: node.end_lineno])
    body = textwrap.dedent(' ' * node.col_offset + body[node.col_offset:] if False else body)
    body = textwrap.dedent(body).replace('__file__', 'ctx.app_file')
    mod_imports, shared, uses_show, uses_file = needs[n]
    head = [f'"""VMouse {n} page. Moved out of vmouse_server.py: edit this file."""']
    head += sorted(set(mod_imports))
    out = '\n'.join(head) + '\n\n\ndef build(ctx):\n'
    for name in shared:
        out += f'    {name} = ctx.{name}\n'
    if uses_show:
        out += '    show_page = ctx.show_page\n'
    out += textwrap.indent(body, '    ') + f'\n    return {n}_page\n'
    compile(out, f'ui/page_{n}.py', 'exec')   # stop here if the generated file is not valid Python
    write_text(f'ui/page_{n}.py', out, nl)

# replace the page functions in vmouse_server.py with calls into the new files
first = min(funcs[f'{n}_page'].lineno for n in NAMES)
ctx_args = ',\n            '.join(f'{x}={x}' for x in sorted(ctx_names))
block = ('        import types\n'
         '        from ui import ' + ', '.join(f'page_{n}' for n in NAMES) + '\n'
         '        ui_ctx = types.SimpleNamespace(\n'
         '            app_file=__file__,\n'
         '            show_page=lambda name: show_page(name),\n'
         f'            {ctx_args}\n'
         '        )\n'
         + ''.join(f'        {n}_page = page_{n}.build(ui_ctx)\n' for n in NAMES))
drop = set()
for n in NAMES:
    node = funcs[f'{n}_page']
    drop.update(range(node.lineno, node.end_lineno + 1))
new_lines = []
for i, line in enumerate(lines, start=1):
    if i == first:
        new_lines.extend(block.rstrip('\n').split('\n'))
    if i in drop:
        continue
    new_lines.append(line)
new_text = '\n'.join(new_lines)
compile(new_text, P, 'exec')
write_text(P, new_text, nl)
print(f'Part B: pages moved into ui/ ({len(NAMES)} files). vmouse_server.py is now {len(new_lines)} lines (was {len(lines)})')

# make the build include the new files
b = Patcher('build_app.py') if os.path.exists('build_app.py') else None
if b and '"ui"' not in b.text:
    b.sub('"pairing", "web_static",', '"pairing", "web_static", "ui", "ui.page_connection", "ui.page_activity", "ui.page_system", "ui.page_products", "ui.page_about", "ui.page_support",')
    b.save()

# ── Part C: tests, run on every push ─────────────────────────────────────────
for name, b64 in PAYLOAD.items():
    if name.startswith('tests/'):
        write_payload(name, b64)
print('Part C: tests added in tests/ (run them with: python -m pytest tests)')
ci = '.github/workflows/build.yml'
if os.path.exists(ci):
    c = Patcher(ci)
    if 'xvfb' not in c.text:
        c.sub('pip install pytest pyopenssl psutil websockets', 'sudo apt-get update && sudo apt-get install -y xvfb python3-tk\n          pip install pytest pyopenssl psutil websockets pyautogui pillow "qrcode[pil]" pystray python-xlib')
        c.sub('python -m pytest -q tests; else', 'xvfb-run -a python -m pytest -q tests; else')
        c.save()
        print('GitHub test job now runs the full test suite')
print('\nDone. Now run: python vmouse_server.py')
