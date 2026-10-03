"""Build VMouse for the system you are on (Windows, Mac or Linux).

    python build_app.py

Result: dist/VMouse.exe (Windows), dist/VMouse (Linux) or dist/VMouse.app (Mac).
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENTRY = ROOT / "vmouse_server.py"
ASSETS = ROOT / "assets"
PWA = ROOT / "pwa"
ICO = ASSETS / "vmouse.ico"

HIDDEN = [
    "tkinter", "PIL", "PIL.Image", "PIL.ImageTk", "PIL.ImageDraw", "qrcode", "qrcode.image.pil",
    "websockets", "OpenSSL", "psutil", "pyautogui", "pystray",
    "pairing", "web_static", "ui", "ui.page_connection", "ui.page_activity", "ui.page_system", "ui.page_products", "ui.page_about", "ui.page_support", "ui_kit", "tray", "health_handler", "system_handler", "platform_utils",
]
PLATFORM_HIDDEN = {
    "win32": ["pystray._win32"],
    "darwin": ["pystray._darwin"],
    "linux": ["pystray._xorg", "Xlib"],
}


def run(command):
    print(">", " ".join(str(c) for c in command))
    return subprocess.call([str(c) for c in command], cwd=ROOT)


def app_version():
    try:
        text = ENTRY.read_text(encoding="utf-8")
        return re.search(r'APP_VERSION\s*=\s*"([^"]+)"', text).group(1)
    except Exception:
        return "1.0.0"


def make_icns():
    """Mac icon made from the Windows icon."""
    from PIL import Image
    target = ROOT / "build" / "VMouse.icns"
    target.parent.mkdir(exist_ok=True)
    Image.open(ICO).convert("RGBA").resize((512, 512), Image.LANCZOS).save(target)
    return target


def main():
    for needed in (ENTRY, ICO, PWA / "index.html"):
        if not needed.exists():
            raise SystemExit(f"ERROR: {needed.relative_to(ROOT)} not found.")
    platform = sys.platform
    sep = ";" if platform == "win32" else ":"
    command = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--name", "VMouse",
               "--add-data", f"{ASSETS}{sep}assets", "--add-data", f"{PWA}{sep}pwa"]
    if platform == "win32":
        command += ["--onefile", "--windowed", "--icon", ICO]
    elif platform == "darwin":
        command += ["--windowed", "--icon", make_icns(), "--osx-bundle-identifier", "com.brytmatech.vmouse"]
    else:
        command += ["--onefile"]
    for name in HIDDEN + PLATFORM_HIDDEN.get("linux" if platform.startswith("linux") else platform, []):
        command += ["--hidden-import", name]
    command.append(ENTRY)
    code = run(command)
    if code != 0:
        raise SystemExit(code)
    version = app_version()
    dist = ROOT / "dist"
    if platform == "win32":
        out = dist / "VMouse.exe"
    elif platform == "darwin":
        out = dist / "VMouse.app"
        shutil.make_archive(str(dist / f"VMouse-{version}-mac"), "zip", dist, "VMouse.app")
    else:
        out = dist / "VMouse"
        shutil.make_archive(str(dist / f"VMouse-{version}-linux"), "gztar", dist, "VMouse")
    print(f"\nBuilt {out}  (version {version})")


if __name__ == "__main__":
    main()
