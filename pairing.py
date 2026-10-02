"""VMouse pairing and connection security.

- A secret pairing code is created once per PC and shown to phones only through the QR code.
- Every connection must send that code first; wrong codes are rejected and rate limited.
- The Android app connects over TLS (wss) and checks the certificate fingerprint from the QR.
- The iPhone web app connects over plain ws (browsers cannot trust the PC's own certificate),
  still protected by the pairing code, and can be switched off by the user.
"""
import hashlib
import hmac
import json
import os
import secrets
import socket
import ssl
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlencode

WS_SECURE_PORT = 8765
WS_PLAIN_PORT = 8766
HTTP_PORT = 8080
HTTPS_PORT = 8443

MAX_FAILURES = 5
FAIL_WINDOW = 60
BLOCK_SECONDS = 120
FIREWALL_RULE = "VMouse"


class PairingStore:
    """Keeps the pairing code and settings in <data_dir>/pairing.json."""

    def __init__(self, data_dir):
        self.path = Path(data_dir) / "pairing.json"
        self._state = self._load()

    def _load(self):
        try:
            state = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(state, dict):
                state = {}
        except Exception:
            state = {}
        changed = False
        token = state.get("token")
        if not isinstance(token, str) or len(token) < 16:
            state["token"] = secrets.token_urlsafe(18)
            changed = True
        if not isinstance(state.get("allow_web"), bool):
            state["allow_web"] = True
            changed = True
        if changed:
            self._save(state)
        return state

    def _save(self, state):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(state), encoding="utf-8")
            try:
                os.chmod(self.path, 0o600)
            except Exception:
                pass
        except Exception:
            pass

    @property
    def token(self):
        return self._state["token"]

    @property
    def allow_web(self):
        return bool(self._state["allow_web"])

    def set_allow_web(self, value):
        self._state["allow_web"] = bool(value)
        self._save(self._state)

    def reset(self):
        self._state["token"] = secrets.token_urlsafe(18)
        self._save(self._state)
        return self._state["token"]


class PairingGuard:
    """Checks pairing codes and blocks addresses that keep guessing."""

    def __init__(self, store, now=time.monotonic):
        self.store = store
        self._now = now
        self._fails = {}
        self._blocked = {}

    def blocked(self, ip):
        until = self._blocked.get(ip)
        if until is None:
            return False
        if self._now() < until:
            return True
        del self._blocked[ip]
        return False

    def check(self, ip, supplied):
        if self.blocked(ip):
            return False, "blocked"
        ok = False
        if isinstance(supplied, str) and supplied:
            ok = hmac.compare_digest(supplied.encode("utf-8"), self.store.token.encode("utf-8"))
        if ok:
            self._fails.pop(ip, None)
            return True, "ok"
        now = self._now()
        recent = [t for t in self._fails.get(ip, []) if now - t < FAIL_WINDOW]
        recent.append(now)
        self._fails[ip] = recent
        if len(recent) >= MAX_FAILURES:
            self._blocked[ip] = now + BLOCK_SECONDS
            self._fails.pop(ip, None)
        return False, "bad_token"


def cert_fingerprint(cert_path):
    """SHA-1 fingerprint (lowercase hex) of the PC's TLS certificate."""
    pem = Path(cert_path).read_text(encoding="ascii")
    return hashlib.sha1(ssl.PEM_cert_to_DER_cert(pem)).hexdigest()


def make_server_ssl_context(cert_path, key_path):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(str(cert_path), str(key_path))
    return ctx


def pairing_url(ip, token, fingerprint="", tls=True):
    query = urlencode({
        "k": token,
        "wss": WS_SECURE_PORT,
        "ws": WS_PLAIN_PORT,
        "fp": fingerprint or "",
        "tls": 1 if tls else 0,
    })
    return f"http://{ip}:{HTTP_PORT}/?{query}"


# ── Network address ──────────────────────────────────────────────────────────

_VIRTUAL_WORDS = ("loopback", "vethernet", "vmware", "virtualbox", "vbox", "docker",
                  "wsl", "hyper-v", "bluetooth", "tailscale", "zerotier", "vpn", "tap-", "tun")


def _is_private(ip):
    try:
        a, b = (int(x) for x in ip.split(".")[:2])
    except Exception:
        return False
    return a == 10 or (a == 172 and 16 <= b <= 31) or (a == 192 and b == 168)


def _route_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


def candidate_ips():
    """Private IPv4 addresses on real (non-virtual) network adapters: [(name, ip)]."""
    found = []
    try:
        import psutil
        for name, addrs in psutil.net_if_addrs().items():
            if any(w in name.lower() for w in _VIRTUAL_WORDS):
                continue
            for a in addrs:
                if a.family == socket.AF_INET and _is_private(a.address):
                    found.append((name, a.address))
    except Exception:
        pass
    return found


def pick_lan_ip():
    """Best address for phones on the same Wi-Fi (avoids VPN and virtual adapters)."""
    route = _route_ip()
    cands = candidate_ips()
    ips = [ip for _n, ip in cands]
    if route in ips:
        return route
    if ips:
        for prefix in ("192.168.", "10.", "172."):
            for ip in ips:
                if ip.startswith(prefix):
                    return ip
        return ips[0]
    if route and not route.startswith(("127.", "169.254.")):
        return route
    return "127.0.0.1"


def network_hint(ip):
    if ip.startswith("127."):
        return "This PC does not seem to be on a network. Connect it to Wi-Fi first."
    if ip.startswith("169.254."):
        return "This PC has no valid network address yet. Reconnect to Wi-Fi."
    return ""


# ── Windows Firewall ─────────────────────────────────────────────────────────

def firewall_commands():
    ports = f"{WS_SECURE_PORT},{WS_PLAIN_PORT},{HTTP_PORT},{HTTPS_PORT}"
    return (f"netsh advfirewall firewall delete rule name={FIREWALL_RULE} & "
            f"netsh advfirewall firewall add rule name={FIREWALL_RULE} dir=in action=allow "
            f"protocol=TCP localport={ports} profile=private,public")


def open_firewall():
    """Ask Windows (with its permission prompt) to allow VMouse's ports. Returns (ok, message)."""
    if sys.platform != "win32":
        return False, "Firewall setup is only needed on Windows."
    try:
        ps = f"Start-Process cmd -ArgumentList '/c {firewall_commands()}' -Verb RunAs -WindowStyle Hidden"
        subprocess.Popen(["powershell", "-NoProfile", "-Command", ps],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True, "Windows will now ask for permission. Choose Yes, then try your phone again."
    except Exception as e:
        return False, f"Could not start firewall setup: {e}"
