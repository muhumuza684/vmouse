"""
VMouse PC Server v4.0
Powered by Bryt Ma Tech, Uganda
─────────────────────────────────
- WebSocket server (ws://IP:8765)
- HTTPS web server (https://IP:8443)  ← voice + camera on phone
- Beautiful branded QR popup window
- Live connection status
- Accepts both Flutter APK and browser commands
- Voice handler support
"""

import asyncio, json, logging, os, signal, socket, sys, time, threading, ssl
import http.server, socketserver
import pyautogui, websockets

try:
    from voice_handler import handle_voice_command
    VOICE = True
except ImportError:
    VOICE = False

WS_PORT      = 8765
WEB_PORT     = 8443
SENSITIVITY  = 1.5
SCROLL_SPEED = 3

BRAND_PRIMARY = "#6C5CE7"
BRAND_BG      = "#0a0a12"
BRAND_SURFACE = "#111120"
BRAND_TEXT    = "#f0f0f8"
BRAND_MUTED   = "#8888aa"

pyautogui.FAILSAFE = True
pyautogui.PAUSE    = 0.0

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("VMouse")

stats   = dict(moves=0, clicks=0, scrolls=0, keystrokes=0, start_time=time.time())
clients: set = set()


# ── Network ───────────────────────────────────────────────────────────────────

def local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]; s.close(); return ip
    except:
        return "127.0.0.1"


# ── SSL cert ──────────────────────────────────────────────────────────────────

def gen_cert_if_needed():
    if os.path.exists("cert.pem") and os.path.exists("key.pem"):
        return True
    try:
        from OpenSSL import crypto
        k = crypto.PKey(); k.generate_key(crypto.TYPE_RSA, 2048)
        cert = crypto.X509()
        cert.get_subject().CN = local_ip()
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)
        cert.set_issuer(cert.get_subject()); cert.set_pubkey(k); cert.sign(k, "sha256")
        open("cert.pem", "wb").write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        open("key.pem",  "wb").write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
        log.info("SSL cert generated"); return True
    except ImportError:
        log.warning("pyopenssl not found — HTTPS disabled. pip install pyopenssl"); return False
    except Exception as e:
        log.warning(f"Cert gen failed: {e}"); return False


# ── Web server ────────────────────────────────────────────────────────────────

def start_web_server(directory):
    has_ssl = gen_cert_if_needed()
    os.chdir(directory)
    handler = http.server.SimpleHTTPRequestHandler
    handler.log_message = lambda *a: None

    if has_ssl:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain("cert.pem", "key.pem")
        class SSLServer(socketserver.TCPServer):
            def get_request(self):
                conn, addr = self.socket.accept()
                return ctx.wrap_socket(conn, server_side=True), addr
        try:
            with SSLServer(("", WEB_PORT), handler) as httpd:
                log.info(f"HTTPS web server on port {WEB_PORT}")
                httpd.serve_forever()
            return
        except Exception as e:
            log.warning(f"HTTPS failed ({e}), falling back to HTTP:8080")

    with socketserver.TCPServer(("", 8080), handler) as httpd:
        log.info("HTTP web server on port 8080")
        httpd.serve_forever()


# ── QR popup window ───────────────────────────────────────────────────────────

def show_qr_popup(ip, has_ssl):
    try:
        import tkinter as tk
        from PIL import Image, ImageTk, ImageDraw, ImageFont
        import qrcode as qc

        scheme = "https" if has_ssl else "http"
        port   = WEB_PORT if has_ssl else 8080
        web_url = f"{scheme}://{ip}:{port}"
        ws_url  = f"ws://{ip}:{WS_PORT}"

        # QR encodes the WebSocket URL (what the Flutter APK scans)
        qr = qc.QRCode(border=2, error_correction=qc.constants.ERROR_CORRECT_M)
        qr.add_data(ws_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color=BRAND_PRIMARY, back_color="white")
        img = img.resize((240, 240), Image.NEAREST)

        root = tk.Tk()
        root.title("VMouse — Waiting for phone")
        root.configure(bg=BRAND_BG)
        root.resizable(False, False)
        root.attributes("-topmost", True)

        # ── Header ──
        hdr = tk.Frame(root, bg=BRAND_PRIMARY, pady=0)
        hdr.pack(fill="x")
        tk.Label(
            hdr, text="VMouse", font=("Helvetica", 20, "bold"),
            bg=BRAND_PRIMARY, fg="white"
        ).pack(side="left", padx=20, pady=14)
        tk.Label(
            hdr, text="Powered by Bryt Ma Tech, Uganda",
            font=("Helvetica", 8), bg=BRAND_PRIMARY, fg="#d0ccff"
        ).pack(side="right", padx=20, pady=14)

        # ── Status bar ──
        status_frame = tk.Frame(root, bg=BRAND_SURFACE, pady=0)
        status_frame.pack(fill="x", padx=0, pady=0)
        status_var = tk.StringVar(value="  ⚫  No phone connected")
        status_lbl = tk.Label(
            status_frame, textvariable=status_var,
            font=("Helvetica", 10, "bold"), bg=BRAND_SURFACE, fg="#ef4444",
            anchor="w"
        )
        status_lbl.pack(fill="x", padx=16, pady=8)

        # ── QR code ──
        tk.Label(
            root, text="Scan with VMouse app on your phone",
            font=("Helvetica", 11), bg=BRAND_BG, fg=BRAND_MUTED
        ).pack(pady=(16, 8))

        photo = ImageTk.PhotoImage(img)
        qr_lbl = tk.Label(root, image=photo, bg="white", bd=3, relief="flat")
        qr_lbl.pack(padx=32)

        tk.Label(
            root, text=ws_url, font=("Courier", 10),
            bg=BRAND_BG, fg=BRAND_PRIMARY
        ).pack(pady=(10, 4))

        # ── Steps ──
        steps_frame = tk.Frame(root, bg=BRAND_SURFACE, bd=0)
        steps_frame.pack(fill="x", padx=24, pady=(12, 0))
        tk.Label(
            steps_frame, text="How to connect:", font=("Helvetica", 10, "bold"),
            bg=BRAND_SURFACE, fg=BRAND_TEXT
        ).pack(anchor="w", padx=14, pady=(10, 4))
        for step in [
            "1.  Install VMouse APK on your phone",
            "2.  Open the app — it goes straight to scanner",
            "3.  Point at this QR code",
            "4.  Start controlling your PC!",
        ]:
            tk.Label(
                steps_frame, text=step, font=("Helvetica", 10),
                bg=BRAND_SURFACE, fg=BRAND_MUTED
            ).pack(anchor="w", padx=14, pady=1)

        tk.Label(
            root, text=f"Or open Chrome on phone → {web_url}",
            font=("Courier", 8), bg=BRAND_BG, fg="#3a3a5a"
        ).pack(pady=(8, 2))

        # ── Footer ──
        tk.Label(
            root, text="© Bryt Ma Tech, Uganda  •  github.com/muhumuza684",
            font=("Helvetica", 8), bg=BRAND_BG, fg="#2a2a4a"
        ).pack(pady=(4, 0))

        tk.Button(
            root, text="Quit VMouse", font=("Helvetica", 9),
            bg=BRAND_SURFACE, fg="#5a5a7a", bd=0, padx=16, pady=6,
            activebackground="#2a2a3c", activeforeground="#fff",
            command=root.destroy
        ).pack(pady=(6, 16))

        # ── Live status updater ──
        def update_status():
            n = len(clients)
            if n > 0:
                status_var.set(f"  🟢  {n} phone{'s' if n > 1 else ''} connected")
                status_lbl.config(fg="#22c55e")
                root.title("VMouse — Phone Connected!")
            else:
                status_var.set("  ⚫  No phone connected")
                status_lbl.config(fg="#ef4444")
                root.title("VMouse — Waiting for phone")
            root.after(1000, update_status)

        root.after(1000, update_status)
        root.mainloop()

    except Exception as e:
        log.warning(f"QR popup failed: {e} — printing to console")
        try:
            import qrcode as qc
            q = qc.QRCode(border=1)
            q.add_data(f"ws://{ip}:{WS_PORT}")
            q.make(fit=True); q.print_ascii(invert=True)
        except:
            pass


# ── Command handler ───────────────────────────────────────────────────────────

def handle_cmd(data: dict):
    """
    Accepts commands from BOTH Flutter APK and browser client.
    Flutter uses: move, click, double_click, scroll, key, shortcut, type, ping
    Browser uses: move, click, scroll, hotkey, keypress, open_app
    """
    t = data.get("type", "")

    if VOICE and handle_voice_command(data):
        stats["keystrokes"] += 1; return None

    # ── Ping / heartbeat ──
    if t == "ping":
        return {"type": "pong"}

    # ── Mouse move ──
    elif t == "move":
        pyautogui.moveRel(
            float(data.get("dx", 0)) * SENSITIVITY,
            float(data.get("dy", 0)) * SENSITIVITY,
            duration=0
        )
        stats["moves"] += 1

    # ── Click (single) ──
    elif t == "click":
        btn = data.get("button", "left")
        n   = int(data.get("clicks", 1))
        pyautogui.click(button=btn, clicks=n, interval=0.05)
        log.info(f"Click: {btn} x{n}"); stats["clicks"] += 1

    # ── Double click (Flutter shorthand) ──
    elif t == "double_click":
        pyautogui.doubleClick()
        log.info("Double click"); stats["clicks"] += 1

    # ── Scroll ──
    elif t == "scroll":
        pyautogui.scroll(int(data.get("dy", 0)) * SCROLL_SPEED)
        stats["scrolls"] += 1

    # ── Shortcut (Flutter: "ctrl+c" string) ──
    elif t == "shortcut":
        raw = data.get("keys", "")
        parts = [k.strip().replace("super", "win").replace("win+", "win") for k in raw.split("+")]
        if parts:
            pyautogui.hotkey(*parts)
            log.info(f"Shortcut: {raw}"); stats["keystrokes"] += 1

    # ── Hotkey (browser: list of keys) ──
    elif t == "hotkey":
        keys = [k.replace("super", "win") for k in data.get("keys", [])]
        if keys:
            pyautogui.hotkey(*keys)
            log.info(f"Hotkey: {'+'.join(keys)}"); stats["keystrokes"] += 1

    # ── Key press (Flutter: single key name) ──
    elif t == "key":
        key_map = {
            "left": "left", "right": "right", "up": "up", "down": "down",
            "space": "space", "enter": "enter", "backspace": "backspace",
            "delete": "delete", "tab": "tab", "esc": "escape",
            "home": "home", "end": "end", "page_up": "pageup",
            "page_down": "pagedown", "insert": "insert",
            "f1":"f1","f2":"f2","f3":"f3","f4":"f4","f5":"f5",
            "printscreen": "printscreen",
        }
        raw = data.get("key", "").lower()
        key = key_map.get(raw, raw)
        pyautogui.press(key)
        log.info(f"Key: {key}"); stats["keystrokes"] += 1

    # ── Keypress (browser: text or key) ──
    elif t == "keypress":
        text = data.get("text"); key = data.get("key")
        if text:
            pyautogui.typewrite(str(text), interval=0.04)
            log.info(f"Type: {text!r}")
            stats["keystrokes"] += 1
            return {"type": "echo", "text": text, "status": "✓ Sent to PC"}
        elif key:
            k = key.replace("super", "win")
            if "+" in k: pyautogui.hotkey(*k.split("+"))
            else: pyautogui.press(k)
            log.info(f"Key (keypress): {key}"); stats["keystrokes"] += 1

    # ── Type text (Flutter) ──
    elif t == "type":
        text = data.get("text", "")
        if text:
            pyautogui.typewrite(str(text), interval=0.04)
            log.info(f"Type: {text!r}"); stats["keystrokes"] += 1
            return {"type": "echo", "text": text, "status": "✓ Sent to PC"}

    # ── Open app (browser/voice) ──
    elif t == "open_app":
        app = data.get("app", "").strip()
        if app:
            pyautogui.press("win"); time.sleep(0.6)
            pyautogui.typewrite(app, interval=0.05); time.sleep(0.5)
            pyautogui.press("enter")
            log.info(f"Open app: {app}"); stats["keystrokes"] += 1
            return {"type": "echo", "text": f"Opening {app}...", "status": "✓ Done"}

    return None


# ── WebSocket handler ─────────────────────────────────────────────────────────

async def ws_handler(ws):
    addr = ws.remote_address
    clients.add(ws)
    log.info(f"📱 Phone connected: {addr}")
    try:
        async for msg in ws:
            try:
                data  = json.loads(msg)
                reply = handle_cmd(data)
                if reply:
                    await ws.send(json.dumps(reply))
            except json.JSONDecodeError:
                log.warning(f"Bad JSON: {msg[:60]}")
            except Exception as e:
                log.error(f"Cmd error: {e}")
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        clients.discard(ws)
        log.info(f"📵 Phone disconnected: {addr}")


# ── Status loop ───────────────────────────────────────────────────────────────

async def status_loop():
    while True:
        await asyncio.sleep(30)
        up = int(time.time() - stats["start_time"])
        h, r = divmod(up, 3600); m, s = divmod(r, 60)
        log.info(
            f"uptime={h:02d}:{m:02d}:{s:02d} | clients={len(clients)} | "
            f"moves={stats['moves']} clicks={stats['clicks']} "
            f"scrolls={stats['scrolls']} keys={stats['keystrokes']}"
        )


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    ip         = local_ip()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    has_ssl    = gen_cert_if_needed()

    print(f"\n{'='*50}")
    print(f"  VMouse PC Server v4.0")
    print(f"  Powered by Bryt Ma Tech, Uganda")
    print(f"{'='*50}")
    print(f"  IP        : {ip}")
    print(f"  WebSocket : ws://{ip}:{WS_PORT}")
    scheme = "https" if has_ssl else "http"
    port   = WEB_PORT if has_ssl else 8080
    print(f"  Phone app : {scheme}://{ip}:{port}")
    print(f"{'='*50}\n")

    # Web server in background
    threading.Thread(target=start_web_server, args=(script_dir,), daemon=True).start()
    time.sleep(0.4)

    # QR popup in background
    threading.Thread(target=show_qr_popup, args=(ip, has_ssl), daemon=True).start()

    # WebSocket server (blocking)
    async def run():
        stop = asyncio.get_event_loop().create_future()
        signal.signal(signal.SIGINT,  lambda *_: stop.set_result(None) if not stop.done() else None)
        signal.signal(signal.SIGTERM, lambda *_: stop.set_result(None) if not stop.done() else None)
        async with websockets.serve(ws_handler, "0.0.0.0", WS_PORT):
            log.info(f"WebSocket listening on 0.0.0.0:{WS_PORT}")
            asyncio.create_task(status_loop())
            await stop
        log.info(f"Stopped. Session stats: {stats}")

    asyncio.run(run())


if __name__ == "__main__":
    main()
