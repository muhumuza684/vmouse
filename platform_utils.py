"""Operating-system differences for VMouse (Windows, Mac, Linux) in one place."""
import os
import re
import shutil
import subprocess
import sys
import time

IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")

POWER_ACTIONS = ("shutdown", "restart", "sleep", "lock", "logout", "hibernate", "cancel")


def power_command(action):
    """Return (command, message) for a power action on this system, or None if unsupported."""
    if IS_WIN:
        table = {
            "shutdown": ("shutdown /s /t 5", "Shutting down in 5 seconds..."),
            "restart": ("shutdown /r /t 5", "Restarting in 5 seconds..."),
            "sleep": ("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", "Entering sleep mode..."),
            "lock": ("rundll32.exe user32.dll,LockWorkStation", "Locking workstation..."),
            "logout": ("shutdown /l", "Logging out..."),
            "hibernate": ("shutdown /h", "Hibernating..."),
            "cancel": ("shutdown /a", "Cancelling pending shutdown/restart..."),
        }
    elif IS_MAC:
        table = {
            "shutdown": ("osascript -e 'tell app \"System Events\" to shut down'", "Shutting down..."),
            "restart": ("osascript -e 'tell app \"System Events\" to restart'", "Restarting..."),
            "sleep": ("pmset sleepnow", "Entering sleep mode..."),
            "lock": ("pmset displaysleepnow", "Locking the screen..."),
            "logout": ("osascript -e 'tell app \"System Events\" to log out'", "Logging out..."),
            "hibernate": ("pmset sleepnow", "Entering sleep mode..."),
        }
    else:
        table = {
            "shutdown": ("sleep 5 && systemctl poweroff", "Shutting down in 5 seconds..."),
            "restart": ("sleep 5 && systemctl reboot", "Restarting in 5 seconds..."),
            "sleep": ("systemctl suspend", "Entering sleep mode..."),
            "lock": ("loginctl lock-session", "Locking the screen..."),
            "logout": ("loginctl terminate-session ${XDG_SESSION_ID}", "Logging out..."),
            "hibernate": ("systemctl hibernate", "Hibernating..."),
        }
    return table.get(action)


def safe_commands():
    """Read-only diagnostic commands a paired phone may run, per system."""
    if IS_WIN:
        return {"ipconfig", "systeminfo", "tasklist", "ping", "tracert", "netstat", "echo", "dir",
                "where", "find", "findstr", "whoami", "hostname", "ver", "date", "time"}
    base = {"hostname", "whoami", "uname", "uptime", "date", "df", "ping", "echo"}
    if IS_MAC:
        return base | {"ifconfig", "netstat", "sw_vers", "vm_stat"}
    return base | {"ip", "ifconfig", "netstat", "free", "lsb_release"}


def adapt_keys(keys):
    """Translate key names from the phone to the names PyAutoGUI uses on this system."""
    out = []
    for k in keys:
        k = str(k).strip().lower()
        if not k:
            continue
        if k in ("super", "win", "windows", "meta", "cmd"):
            k = "command" if IS_MAC else ("win" if IS_WIN else "winleft")
        elif IS_MAC and k in ("ctrl", "control"):
            k = "command"
        out.append(k)
    return out


def open_app(app, pyautogui=None):
    """Start a program by name. Returns (ok, message)."""
    app = (app or "").strip()
    if not app:
        return False, "No app name"
    if IS_WIN:
        pyautogui.press("win")
        time.sleep(0.6)
        pyautogui.typewrite(app, interval=0.05)
        time.sleep(0.5)
        pyautogui.press("enter")
        return True, f"Opening {app}..."
    if not re.fullmatch(r"[\w .+\-]{1,60}", app):
        return False, "That app name is not allowed"
    try:
        if IS_MAC:
            subprocess.Popen(["open", "-a", app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True, f"Opening {app}..."
        exe = shutil.which(app) or shutil.which(app.lower().replace(" ", "-"))
        if not exe:
            return False, f"'{app}' was not found on this computer"
        subprocess.Popen([exe], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True, f"Opening {app}..."
    except Exception as e:
        return False, str(e)


def startup_notice():
    """Something the person must do once for mouse control to work, or None."""
    if IS_MAC:
        return "Mac: allow VMouse under System Settings, Privacy and Security, Accessibility, so it can move the mouse."
    if IS_LINUX and os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland":
        return "Linux: mouse control needs an X11 session. Pick the Xorg option on the login screen."
    return None
