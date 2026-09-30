from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
ENTRY = ROOT / "vmouse_server.py"
ASSETS = ROOT / "assets"
ICON = ASSETS / "vmouse.ico"

def run(command):
    print(">", " ".join(map(str, command)))
    return subprocess.call(command, cwd=ROOT)

def main():

    if not ENTRY.exists():
        raise SystemExit("ERROR: vmouse_server.py not found.")

    if not ICON.exists():
        raise SystemExit("ERROR: assets/vmouse.ico not found.")

    packages = [
        "pyinstaller",
        "pillow",
        "qrcode[pil]",
        "websockets",
        "pyautogui",
        "pyopenssl",
    ]

    install_code = run([
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        *packages,
    ])

    if install_code != 0:
        raise SystemExit(install_code)

    command = [
        sys.executable,
        "-m",
        "PyInstaller",

        "--noconfirm",
        "--clean",

        "--onefile",
        "--windowed",

        "--name",
        "VMouse",

        "--icon",
        str(ICON),

        "--add-data",
        f"{ASSETS};assets",

        "--hidden-import",
        "tkinter",

        "--hidden-import",
        "PIL",

        "--hidden-import",
        "PIL.Image",

        "--hidden-import",
        "PIL.ImageTk",

        "--hidden-import",
        "qrcode",

        "--hidden-import",
        "qrcode.image.pil",

        "--hidden-import",
        "websockets",

        "--hidden-import",
        "OpenSSL",

        str(ENTRY),
    ]

    code = run(command)

    if code != 0:
        raise SystemExit(code)

    exe = ROOT / "dist" / "VMouse.exe"

    if not exe.exists():
        raise SystemExit("ERROR: PyInstaller finished but VMouse.exe does not exist.")

    print("")
    print("======================================")
    print(" VMOUSE WINDOWS BUILD SUCCESS")
    print("======================================")
    print(exe)
    print("")
    print("WINDOWS STACK:")
    print("Python + Tkinter + PyInstaller")
    print("Flutter is NOT used for this EXE.")
    print("======================================")

if __name__ == "__main__":
    main()
