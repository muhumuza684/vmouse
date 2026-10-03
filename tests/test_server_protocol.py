"""Starts the real server and checks pairing end to end. Skipped where no display is available."""
import asyncio
import json
import os
import shutil
import socket
import ssl
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
pytestmark = pytest.mark.skipif(
    not (shutil.which("xvfb-run") or os.environ.get("DISPLAY")), reason="needs a display (xvfb-run)")


def wait_port(port, timeout=40):
    end = time.time() + timeout
    while time.time() < end:
        with socket.socket() as s:
            s.settimeout(0.5)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(0.4)
    return False


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    data = tmp_path_factory.mktemp("lad")
    env = dict(os.environ, LOCALAPPDATA=str(data), VMOUSE_HEADLESS="1")
    cmd = [sys.executable, str(ROOT / "vmouse_server.py")]
    if shutil.which("xvfb-run") and not os.environ.get("DISPLAY"):
        cmd = ["xvfb-run", "-a"] + cmd
    proc = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            start_new_session=(os.name != "nt"))
    try:
        assert wait_port(8766), "server did not start"
        token = json.loads((data / "VMouse" / "pairing.json").read_text())["token"]
        yield token
    finally:
        try:
            if os.name == "nt":
                proc.kill()
            else:
                import signal
                os.killpg(proc.pid, signal.SIGKILL)
        except Exception:
            proc.kill()
        proc.wait(timeout=15)


def tls():
    c = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    c.check_hostname = False
    c.verify_mode = ssl.CERT_NONE
    return c


async def talk(uri, first, **kw):
    import websockets
    import inspect
    if "proxy" in inspect.signature(websockets.connect).parameters:
        kw.setdefault("proxy", None)
    async with websockets.connect(uri, **kw) as ws:
        await ws.send(json.dumps(first))
        return json.loads(await ws.recv())


def run(coro):
    return asyncio.run(coro)


def test_right_code_is_accepted(server):
    assert run(talk("ws://127.0.0.1:8766", {"type": "auth", "token": server}))["type"] == "auth_ok"
    assert run(talk("wss://127.0.0.1:8765", {"type": "auth", "token": server}, ssl=tls()))["type"] == "auth_ok"


def test_commands_without_pairing_are_refused(server):
    reply = run(talk("ws://127.0.0.1:8766", {"type": "move", "dx": 5, "dy": 5}))
    assert reply == {"type": "auth_failed", "reason": "auth_required"}


def test_page_is_served_but_source_is_not(server):
    import urllib.error
    import urllib.request
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    assert opener.open("http://127.0.0.1:8080/", timeout=5).status == 200
    with pytest.raises(urllib.error.HTTPError) as err:
        opener.open("http://127.0.0.1:8080/vmouse_server.py", timeout=5)
    assert err.value.code == 404


def test_wrong_codes_get_blocked_last(server):
    for i in range(5):
        assert run(talk("ws://127.0.0.1:8766", {"type": "auth", "token": f"bad{i}"}))["type"] == "auth_failed"
    assert run(talk("ws://127.0.0.1:8766", {"type": "auth", "token": server}))["reason"] == "blocked"
