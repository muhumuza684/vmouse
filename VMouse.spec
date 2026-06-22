# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\LENOVO\\Desktop\\vmouse\\vmouse_server.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['pyautogui', 'PIL', 'PIL._tkinter_finder', 'qrcode', 'qrcode.image.pil', 'websockets', 'websockets.legacy', 'websockets.legacy.server', 'OpenSSL', 'tkinter', 'pystray'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='VMouse',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
