"""
System control module for VMouse PC server.
Handles power operations and a restricted set of diagnostic CMD commands.

SECURITY NOTE:
This module intentionally only allow-lists read-only, non-destructive
commands. It does NOT attempt to block "dangerous" commands via a
keyword denylist, because denylists are trivially bypassed (aliases,
alternate flags, PowerShell equivalents, path tricks, etc.). Anything
not explicitly on SAFE_COMMANDS is rejected outright rather than run.
If you need broader remote command execution, pair it with per-request
authentication (see vmouse_server.py TODO) rather than widening this list.
"""

import subprocess
from typing import Dict, Any


def execute_system_power(action: str) -> Dict[str, Any]:
    """Execute power actions: shutdown, restart, sleep, lock."""
    actions = {
        "shutdown": ("shutdown /s /t 5", "Shutting down in 5 seconds..."),
        "restart": ("shutdown /r /t 5", "Restarting in 5 seconds..."),
        "sleep": ("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", "Entering sleep mode..."),
        "lock": ("rundll32.exe user32.dll,LockWorkStation", "Locking workstation..."),
        "logout": ("shutdown /l", "Logging out..."),
        "hibernate": ("shutdown /h", "Hibernating..."),
        "cancel": ("shutdown /a", "Cancelling pending shutdown/restart..."),
    }

    if action in actions:
        cmd, message = actions[action]
        try:
            subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"status": "success", "action": action, "message": message}
        except Exception as e:
            return {"status": "error", "action": action, "message": str(e)}
    else:
        return {"status": "error", "message": f"Unknown action: {action}"}


# Allow-list of read-only diagnostic commands. Anything not in this set
# is rejected. This is deliberately an allow-list, not a denylist.
SAFE_COMMANDS = {
    "ipconfig", "systeminfo", "tasklist", "ping", "tracert", "netstat",
    "echo", "dir", "where", "find", "findstr", "whoami", "hostname",
    "ver", "date", "time",
}

# Commands that never run, even if a caller adds them to SAFE_COMMANDS later.
# Belt-and-suspenders — the real protection is the allow-list above.
_HARD_BLOCKED = {
    "del", "erase", "format", "rd", "rmdir", "reg", "sc", "net",
    "powershell", "cmd", "wmic", "taskkill", "diskpart", "bcdedit",
    "attrib", "cipher", "runas", "shutdown",
}


def execute_custom_command(command: str) -> Dict[str, Any]:
    """Run a diagnostic CMD command, restricted to an allow-list."""
    if not command or not command.strip():
        return {"status": "error", "message": "Empty command"}

    command = command.strip()
    cmd_parts = command.split()
    base_cmd = cmd_parts[0].lower() if cmd_parts else ""

    if base_cmd in _HARD_BLOCKED:
        return {
            "status": "blocked",
            "message": f"'{base_cmd}' is not permitted over remote command execution",
        }

    if base_cmd not in SAFE_COMMANDS:
        return {
            "status": "blocked",
            "message": f"'{base_cmd}' is not on the allowed command list. "
                       f"Allowed: {', '.join(sorted(SAFE_COMMANDS))}",
        }

    # Reject shell metacharacters that could chain a second, unvetted command
    # onto an otherwise-safe one (e.g. "echo hi & del file").
    if any(ch in command for ch in ("&", "|", ";", "`", "$(", ">", "<")):
        return {"status": "blocked", "message": "Command chaining/redirection is not permitted"}

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=15)
        return {
            "status": "success",
            "output": result.stdout,
            "error": result.stderr if result.stderr else None
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Command timed out"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
