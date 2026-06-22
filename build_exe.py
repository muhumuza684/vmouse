"""
build_exe.py — builds VMouse.exe (single file, no Python needed on target PC)
Powered by Bryt Ma Tech, Uganda

Run:   python build_exe.py
Output: dist/VMouse.exe  — share this with PC users
"""

import subprocess, sys, os

print("\n" + "="*52)
print("  VMouse Build Tool")
print("  Powered by Bryt Ma Tech, Uganda")
print("="*52)

# Install required packages
pkgs = [
    "pyinstaller",
    "pystray",
    "pillow",
    "qrcode[pil]",
    "websockets",
    "pyautogui",
    "pyopenssl",
]

print("\n[1/3] Installing dependencies...")
for p in pkgs:
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", p, "-q"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"  ✓  {p}")

print("\n[2/3] Building VMouse.exe...")

# Copy voice_handler if it exists alongside this script
script_dir  = os.path.dirname(os.path.abspath(__file__))
server_file = os.path.join(script_dir, "vmouse_server.py")
voice_file  = os.path.join(script_dir, "voice_handler.py")

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--onefile",
    "--windowed",
    "--name", "VMouse",
    "--hidden-import", "pyautogui",
    "--hidden-import", "PIL",
    "--hidden-import", "PIL._tkinter_finder",
    "--hidden-import", "qrcode",
    "--hidden-import", "qrcode.image.pil",
    "--hidden-import", "websockets",
    "--hidden-import", "websockets.legacy",
    "--hidden-import", "websockets.legacy.server",
    "--hidden-import", "OpenSSL",
    "--hidden-import", "tkinter",
    "--hidden-import", "pystray",
]

if os.path.exists(voice_file):
    cmd += ["--add-data", f"{voice_file};."]

cmd.append(server_file)

result = subprocess.run(cmd)

print("\n[3/3] Result:")
if result.returncode == 0:
    exe_path = os.path.join(script_dir, "dist", "VMouse.exe")
    size_mb  = os.path.getsize(exe_path) / 1_048_576 if os.path.exists(exe_path) else 0
    print("\n" + "="*52)
    print("  ✅  BUILD SUCCESSFUL!")
    print(f"  📦  dist/VMouse.exe  ({size_mb:.1f} MB)")
    print("  📲  Share VMouse.exe with PC users")
    print("  📱  Share VMouse.apk with phone users")
    print("="*52)
    print("\n  How it works:")
    print("  PC user  → double-click VMouse.exe → QR appears")
    print("  Phone    → open VMouse app → scan QR → done!")
    print("="*52 + "\n")
else:
    print("\n  ❌  Build failed — check errors above")
    sys.exit(1)
