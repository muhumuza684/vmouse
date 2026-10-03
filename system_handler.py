"""
System control module for VMouse PC server.
Handles power operations and a restricted set of diagnostic commands.

SECURITY NOTE:
Only an allow-list of read-only commands can run. Anything not on the list is rejected,
and shell chaining characters are refused. Every connection must also pass the pairing check
in vmouse_server.py before it can reach this module.
"""
import subprocess
from typing import Dict, Any

import platform_utils


def execute_system_power(action: str) -> Dict[str, Any]:
    """Execute power actions: shutdown, restart, sleep, lock, logout, hibernate, cancel."""
    if action not in platform_utils.POWER_ACTIONS:
        return {"status": "error", "message": f"Unknown action: {action}"}
    entry = platform_utils.power_command(action)
    if entry is None:
        return {"status": "error", "action": action, "message": "This action is not available on this computer"}
    cmd, message = entry
    try:
        subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"status": "success", "action": action, "message": message}
    except Exception as e:
        return {"status": "error", "action": action, "message": str(e)}


SAFE_COMMANDS = platform_utils.safe_commands()

# Commands that never run, even if someone adds them to SAFE_COMMANDS later.
_HARD_BLOCKED = {
    "del", "erase", "format", "rd", "rmdir", "rm", "reg", "sc", "net", "powershell", "cmd", "wmic",
    "taskkill", "kill", "diskpart", "bcdedit", "attrib", "cipher", "runas", "shutdown", "reboot",
    "sudo", "su", "chmod", "chown", "dd", "mkfs", "curl", "wget", "bash", "sh", "python",
}


def execute_custom_command(command: str) -> Dict[str, Any]:
    """Run a diagnostic command, restricted to an allow-list."""
    if not command or not command.strip():
        return {"status": "error", "message": "Empty command"}
    command = command.strip()
    cmd_parts = command.split()
    base_cmd = cmd_parts[0].lower() if cmd_parts else ""
    if base_cmd in _HARD_BLOCKED:
        return {"status": "blocked", "message": f"'{base_cmd}' is not permitted over remote command execution"}
    if base_cmd not in SAFE_COMMANDS:
        return {
            "status": "blocked",
            "message": f"'{base_cmd}' is not on the allowed command list. Allowed: {', '.join(sorted(SAFE_COMMANDS))}",
        }
    if any(ch in command for ch in ("&", "|", ";", "`", "$(", ">", "<", "\n", "\r")):
        return {"status": "blocked", "message": "Command chaining/redirection is not permitted"}
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=15)
        return {"status": "success", "output": result.stdout, "error": result.stderr if result.stderr else None}
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Command timed out"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
