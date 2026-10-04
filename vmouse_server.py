from pathlib import Path


# VMouse resource directory.
# Development: directory containing vmouse_server.py.
# PyInstaller: directory containing bundled resources.
def vmouse_resource(name):
    """
    Return a path to a bundled/read-only application resource.

    PyInstaller one-file builds expose bundled files through
    sys._MEIPASS. During normal Python execution resources live
    beside vmouse_server.py.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent

    return str(base / name)



"""
VMouse PC Server 1.0.0
Powered by Bryt Ma Tech, Uganda
─────────────────────────────────
- WebSocket server (ws://IP:8765)
- HTTPS web server (https://IP:8443)  ← voice + camera on phone
- Beautiful branded QR popup window
- Live connection status
- Accepts both Flutter APK and browser commands
- Voice handler support
"""

import os
import asyncio, json, logging, os, signal, socket, sys, time, threading, ssl
import http.server, socketserver
import pyautogui, websockets

try:
    from voice_handler import handle_voice_command
    VOICE = True
except ImportError:
    VOICE = False

# NEW: system power / diagnostic command / health monitoring
from health_handler import get_pc_health, analyze_pc_health
from system_handler import execute_system_power, execute_custom_command

WS_PORT      = 8765
WEB_PORT     = 8443

# Writable per-user runtime directory.
# This avoids trying to write certificates inside a
# PyInstaller temporary/read-only resource directory.
VMOUSE_DATA_DIR = Path(
    os.environ.get("LOCALAPPDATA", str(Path.home()))
) / "VMouse"

VMOUSE_CERT_PATH = VMOUSE_DATA_DIR / "cert.pem"
VMOUSE_KEY_PATH  = VMOUSE_DATA_DIR / "key.pem"

import contextlib
import functools
import pairing
import web_static

WS_PLAIN_PORT = pairing.WS_PLAIN_PORT
HTTP_PORT = pairing.HTTP_PORT
PAIRING_STORE = pairing.PairingStore(VMOUSE_DATA_DIR)
PAIRING_GUARD = pairing.PairingGuard(PAIRING_STORE)
LOOP = None  # the asyncio loop, set in main()
import ui_kit
import tray

APP_VERSION = "1.0.0"
import platform_utils
STATUS_PORT = 8764  # localhost-only JSON status feed for the Electron desktop app
SENSITIVITY  = 1.5
SCROLL_SPEED = 3

BRAND_PRIMARY = "#6D5FE8"
BRAND_BG      = "#000000"
BRAND_SURFACE = "#12111F"
BRAND_TEXT    = "#F1F0FA"
BRAND_MUTED   = "#8B8AA3"

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

# Message types that do real work (psutil sampling, subprocess calls) and
# must NOT run directly on the event loop thread, or every connected
# phone's mouse/keyboard input stalls for the duration of the call.
HEAVY_COMMAND_TYPES = {"system_power", "system_command", "get_health"}


# ── Network ───────────────────────────────────────────────────────────────────

def local_ip():
    return pairing.pick_lan_ip()


# ── SSL cert ──────────────────────────────────────────────────────────────────

def gen_cert_if_needed():
    """
    Ensure the VMouse HTTPS certificate and private key exist
    in the writable per-user VMouse data directory.
    """
    cert_path = VMOUSE_CERT_PATH
    key_path = VMOUSE_KEY_PATH

    try:
        cert_path.parent.mkdir(parents=True, exist_ok=True)

        if cert_path.exists() and key_path.exists():
            return True

        from OpenSSL import crypto

        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 2048)

        cert = crypto.X509()
        cert.get_subject().C = "UG"
        cert.get_subject().ST = "Uganda"
        cert.get_subject().L = "Kampala"
        cert.get_subject().O = "Bryt Ma Tech Uganda"
        cert.get_subject().OU = "VMouse"
        cert.get_subject().CN = "VMouse"

        cert.set_serial_number(int(time.time()))
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)

        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k, "sha256")

        cert_path.write_bytes(
            crypto.dump_certificate(
                crypto.FILETYPE_PEM,
                cert
            )
        )

        key_path.write_bytes(
            crypto.dump_privatekey(
                crypto.FILETYPE_PEM,
                k
            )
        )

        log.info(
            "VMouse HTTPS certificate created: %s",
            cert_path
        )

        return True

    except ImportError:
        log.warning(
            "pyopenssl not found ? HTTPS disabled. "
            "Install with: pip install pyopenssl"
        )
        return False

    except Exception as e:
        log.exception(
            "Unable to create VMouse HTTPS certificate: %s",
            e
        )
        return False



def pwa_directory():
    """Folder with the iPhone web app. Only this folder is ever served."""
    path = Path(vmouse_resource("pwa"))
    if not path.exists():
        try:
            path.mkdir(parents=True, exist_ok=True)
            (path / "index.html").write_text(
                "<!doctype html><title>VMouse</title><p>The VMouse web app is not installed on this PC yet.</p>",
                encoding="utf-8")
        except Exception:
            pass
    return path


def start_web_server(directory=None):
    folder = pwa_directory()
    try:
        web_static.serve_http(folder, HTTP_PORT)
        log.info(f"Web app on http://0.0.0.0:{HTTP_PORT}")
    except Exception as e:
        log.warning(f"Web app (http) could not start: {e}")
    if gen_cert_if_needed():
        try:
            web_static.serve_https(folder, WEB_PORT, VMOUSE_CERT_PATH, VMOUSE_KEY_PATH)
            log.info(f"Web app on https://0.0.0.0:{WEB_PORT}")
        except Exception as e:
            log.warning(f"Web app (https) could not start: {e}")


# ── QR popup window ───────────────────────────────────────────────────────────


def show_qr_popup(ip, has_ssl):
    try:
        import tkinter as tk
        from PIL import Image, ImageTk
        import qrcode as qc
        import webbrowser
        import sys
        import os

        scheme = "https" if has_ssl else "http"
        port = WEB_PORT if has_ssl else 8080

        web_url = f"http://{ip}:{HTTP_PORT}"
        ws_url = f"{'wss' if has_ssl else 'ws'}://{ip}:{WS_PORT if has_ssl else WS_PLAIN_PORT}"

        # ----------------------------------------------------
        # QR displayed BY THE PC.
        # The phone scans this.
        # ----------------------------------------------------
        def current_pair_url():
            fp = ""
            if has_ssl:
                try:
                    fp = pairing.cert_fingerprint(VMOUSE_CERT_PATH)
                except Exception:
                    fp = ""
            return pairing.pairing_url(ip, PAIRING_STORE.token, fp, tls=bool(fp))

        def make_qr_image():
            qr = qc.QRCode(
                border=2,
                box_size=6,
                error_correction=qc.constants.ERROR_CORRECT_M
            )
            qr.add_data(current_pair_url())
            qr.make(fit=True)
            return qr.make_image(
                fill_color="#12111F",
                back_color="white"
            ).convert("RGB")

        qr_img = make_qr_image()

        base_dir = getattr(
            sys,
            "_MEIPASS",
            os.path.dirname(os.path.abspath(__file__))
        )

        icon_path = os.path.join(
            base_dir,
            "assets",
            "vmouse.ico"
        )

        logo_path = os.path.join(
            base_dir,
            "assets",
            "vmouse_logo.png"
        )

        # ----------------------------------------------------
        # Main Windows application
        # ----------------------------------------------------
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("BrytMaTech.VMouse")
        except Exception:
            pass
        root = tk.Tk()

        # VMOUSE_08C_DESKTOP_POLISH

        # VMouse desktop window configuration.
        try:
            root.title("VMouse - PC Control Center")
        except Exception:
            pass

        try:
            root.minsize(1100, 700)
        except Exception:
            pass

        try:
            root.state("zoomed")
        except Exception:
            try:
                root.geometry("1280x800")
            except Exception:
                pass

        # VMouse application icon.
        try:
            _vmouse_icon = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "assets",
                "vmouse.ico",
            )

            if os.path.exists(_vmouse_icon):
                root.iconbitmap(_vmouse_icon)
        except Exception:
            pass

        root.title("VMouse - PC Control Center")
        root.configure(bg="#000000")

        root.resizable(True, True)
        root.minsize(1050, 700)

        # ----------------------------------------------------
        # Official VMouse application icon
        # ----------------------------------------------------
        try:
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
        except Exception:
            pass

        try:
            logo_image = Image.open(logo_path).convert("RGBA")
            logo_image.thumbnail((64, 64), Image.LANCZOS)
            root_logo = ImageTk.PhotoImage(logo_image)
            root.iconphoto(True, root_logo)
            root._vmouse_root_logo = root_logo
        except Exception:
            pass

        # Open maximized, but remain a normal resizable window.
        try:
            root.state("zoomed")
        except Exception:
            root.geometry("1280x800")

        # ============================================================
        # VMOUSE PREMIUM DESIGN SYSTEM
        # ============================================================

        # ============================================================
        # VMOUSE PREMIUM COLOR SYSTEM
        # ============================================================
        #
        # Deep navy  = application shell/background
        # Blue-teal  = cards and elevated surfaces
        # Teal       = primary actions / active states
        # Light teal = secondary highlights
        # Off-white  = primary text
        # Muted      = secondary text
        # Border     = structural separators
        # Green      = successful/connected states
        # Coral      = warnings/errors
        #
        # Keep semantic colors separate so the interface does not
        # become visually dominated by one color.
        # ============================================================

        NAVY   = "#0B0A14"
        OFF    = "#F1F0FA"
        TEAL   = "#A79EF5"
        CORAL  = "#E5484D"

        # Colors taken from the VMouse phone app
        BG = "#000000"
        SIDEBAR = "#0B0A14"

        SURFACE = "#12111F"
        SURFACE2 = "#1F1F2B"

        PRIMARY = "#6D5FE8"
        PRIMARY2 = "#A79EF5"

        TEXT = "#F1F0FA"
        MUTED = "#8B8AA3"
        BORDER = "#2A2940"

        GREEN = "#3DDC97"
        RED = "#E5484D"

        WHITE = "#FFFFFF"

        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=1)

        # ----------------------------------------------------
        # SIDEBAR
        # ----------------------------------------------------
        sidebar = tk.Frame(
            root,
            bg=SIDEBAR,
            width=235
        )

        sidebar.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        sidebar.grid_propagate(False)

        # Brand
        brand = tk.Frame(
            sidebar,
            bg=SIDEBAR
        )

        brand.pack(
            fill="x",
            padx=20,
            pady=(24, 28)
        )

        # Official VMouse icon from the repository.
        try:
            logo_img = Image.open(logo_path).convert("RGBA")
            logo_img.thumbnail((46, 46), Image.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)

            logo = tk.Label(
                brand,
                image=logo_photo,
                bg=SIDEBAR,
                bd=0
            )
            logo.image = logo_photo
            logo.pack(side="left")
        except Exception:
            # Keep the application usable if the icon cannot be loaded.
            logo = tk.Label(
                brand,
                text="V",
                font=("Segoe UI", 20, "bold"),
                bg=PRIMARY,
                fg="white",
                width=2,
                height=1
            )
            logo.pack(side="left")

        brand_text = tk.Frame(
            brand,
            bg=SIDEBAR
        )

        brand_text.pack(
            side="left",
            padx=9
        )

        tk.Label(
            brand_text,
            text="VMouse",
            font=("Segoe UI", 18, "bold"),
            bg=SIDEBAR,
            fg=TEXT
        ).pack(anchor="w")

        tk.Label(
            brand_text,
            text="Bryt Ma Tech Uganda",
            font=("Segoe UI", 8),
            bg=SIDEBAR,
            fg=PRIMARY2
        ).pack(anchor="w")

        tk.Label(
            sidebar,
            text="PC CONTROL",
            font=("Segoe UI", 8, "bold"),
            bg=SIDEBAR,
            fg="#A79EF5"
        ).pack(
            anchor="w",
            padx=24,
            pady=(0, 8)
        )

        # ----------------------------------------------------
        # MAIN CONTENT
        # ----------------------------------------------------
        content = tk.Frame(
            root,
            bg=BG
        )

        content.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)

        page = tk.Frame(
            content,
            bg=BG
        )

        page.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=30,
            pady=26
        )

        nav_buttons = {}

        def clear_page():
            for widget in page.winfo_children():
                widget.destroy()

        def card(parent):
            return tk.Frame(
                parent,
                bg=SURFACE,
                highlightbackground=BORDER,
                highlightthickness=1
            )

        _vm_noop = lambda *a, **k: None

        def _vm_sync_scroll(canvas, content, window_id):
            try:
                if not canvas.winfo_exists():
                    return
                canvas.update_idletasks()
                width = max(canvas.winfo_width(), 1)
                canvas.itemconfigure(window_id, width=width)
                height = max(content.winfo_reqheight() + 28, canvas.winfo_height())
                canvas.configure(scrollregion=(0, 0, width, height))
                first, last = canvas.yview()
                if first <= 0 and last >= 1:
                    canvas.yview_moveto(0)
            except Exception:
                pass

        def _vm_attach_scroll(canvas, content, window_id):
            canvas.configure(yscrollincrement=20)
            root._vm_scroll_canvas = canvas
            def sync(event=None):
                _vm_sync_scroll(canvas, content, window_id)
            content.bind("<Configure>", sync, add="+")
            canvas.bind("<Configure>", sync, add="+")
            for ms in (60, 200, 500, 1000, 2000):
                root.after(ms, sync)

        def _vm_on_wheel(event):
            canvas = getattr(root, "_vm_scroll_canvas", None)
            try:
                if canvas is None or not canvas.winfo_exists() or not canvas.winfo_ismapped():
                    return
                num = getattr(event, "num", None)
                if num == 4:
                    steps = -3
                elif num == 5:
                    steps = 3
                else:
                    d = event.delta
                    steps = int(-d / 40) or (-1 if d > 0 else 1)
                first, last = canvas.yview()
                if (steps < 0 and first <= 0) or (steps > 0 and last >= 1):
                    return
                canvas.yview_scroll(steps, "units")
            except Exception:
                pass

        root.bind_all("<MouseWheel>", _vm_on_wheel)
        root.bind_all("<Button-4>", _vm_on_wheel)
        root.bind_all("<Button-5>", _vm_on_wheel)

        def header(title, subtitle):
            tk.Label(
                page,
                text=title,
                font=("Segoe UI", 25, "bold"),
                bg=BG,
                fg=TEXT
            ).pack(anchor="w")

            tk.Label(
                page,
                text=subtitle,
                font=("Segoe UI", 10),
                bg=BG,
                fg=MUTED
            ).pack(
                anchor="w",
                pady=(4, 20)
            )

        # ----------------------------------------------------
        # CONNECTION PAGE
        # ----------------------------------------------------
        import types
        from ui import page_connection, page_activity, page_system, page_products, page_about, page_support
        ui_ctx = types.SimpleNamespace(
            app_file=__file__,
            show_page=lambda name: show_page(name),
            BG=BG,
            BORDER=BORDER,
            CORAL=CORAL,
            GREEN=GREEN,
            LOOP=LOOP,
            MUTED=MUTED,
            PAIRING_STORE=PAIRING_STORE,
            PRIMARY=PRIMARY,
            PRIMARY2=PRIMARY2,
            RED=RED,
            SURFACE=SURFACE,
            SURFACE2=SURFACE2,
            TEXT=TEXT,
            _vm_attach_scroll=_vm_attach_scroll,
            _vm_noop=_vm_noop,
            base_dir=base_dir,
            card=card,
            clients=clients,
            close_all_clients=close_all_clients,
            header=header,
            ip=ip,
            make_qr_image=make_qr_image,
            page=page,
            root=root,
            stats=stats,
            web_url=web_url,
            ws_url=ws_url
        )
        connection_page = page_connection.build(ui_ctx)
        activity_page = page_activity.build(ui_ctx)
        system_page = page_system.build(ui_ctx)
        products_page = page_products.build(ui_ctx)
        about_page = page_about.build(ui_ctx)
        support_page = page_support.build(ui_ctx)

        # ----------------------------------------------------
        # OTHER PAGES
        # ----------------------------------------------------








        nav_icons = {}

        def nav_button(label, page_name, symbol):
            icon_off = ImageTk.PhotoImage(ui_kit.nav_icon_image(page_name, "#8B8AA3"))
            icon_on = ImageTk.PhotoImage(ui_kit.nav_icon_image(page_name, "#A79EF5"))
            nav_icons[page_name] = (icon_off, icon_on)
            button = tk.Button(
                sidebar,
                text=f"   {label}",
                image=icon_off,
                compound="left",
                anchor="w",
                command=lambda: show_page(page_name),
                font=("Segoe UI", 10),
                bg=SIDEBAR,
                fg=MUTED,
                activebackground="#1F1F2B",
                activeforeground=TEXT,
                bd=0,
                padx=18,
                pady=11,
                cursor="hand2"
            )
            button.pack(
                fill="x",
                padx=12,
                pady=2
            )
            nav_buttons[page_name] = button

        nav_button("Connection", "connection", "")
        nav_button("Activity", "activity", "")
        nav_button("System & Health", "system", "")
        nav_button("Other Products", "products", "")
        nav_button("About", "about", "")
        nav_button("Support", "support", "")

        tk.Frame(
            sidebar,
            bg=SIDEBAR
        ).pack(
            fill="both",
            expand=True
        )

        tk.Label(
            sidebar,
            text="VMouse 1.0.0",
            font=("Segoe UI", 8),
            bg=SIDEBAR,
            fg="#A79EF5"
        ).pack(
            anchor="w",
            padx=24
        )

        tk.Label(
            sidebar,
            text="Made in Uganda",
            font=("Segoe UI", 8),
            bg=SIDEBAR,
            fg="#A79EF5"
        ).pack(
            anchor="w",
            padx=24,
            pady=(2, 22)
        )

        def show_page(name):

            clear_page()

            for key, button in nav_buttons.items():
                button.config(bg=SIDEBAR, fg=MUTED, image=nav_icons[key][0])

            nav_buttons[name].config(bg="#1F1F2B", fg=TEXT, image=nav_icons[name][1])

            if name == "connection":
                connection_page()

            elif name == "activity":
                activity_page()

            elif name == "system":
                system_page()

            elif name == "products":
                products_page()

            elif name == "about":
                about_page()

            elif name == "support":
                support_page()

        def quit_app():

            try:
                root.destroy()
            finally:
                os._exit(0)

        root.protocol(
            "WM_DELETE_WINDOW",
            quit_app
        )

        try:
            _vm_tray = tray.attach(root, icon_path, quit_app)
            if _vm_tray is not None:
                def _vm_to_tray(event=None):
                    try:
                        if event is not None and event.widget is root and root.state() == "iconic":
                            root.after(50, root.withdraw)
                    except Exception:
                        pass
                pass  # minimize stays on the taskbar
        except Exception:
            pass
        show_page("connection")
        root.mainloop()

    except Exception as e:
        log.warning(
            f"VMouse PC UI failed: {e}"
        )
        raise
def handle_cmd(data: dict):
    """
    Accepts commands from BOTH Flutter APK and browser client.
    Flutter uses: move, click, double_click, scroll, key, shortcut, type, ping
    Browser uses: move, click, scroll, hotkey, keypress, open_app

    NOTE: this function must stay fast/non-blocking — it runs directly on
    the asyncio event loop thread. Heavy commands (system power, custom
    commands, health checks) are handled separately in ws_handler via
    handle_heavy_cmd(), which offloads them to a thread pool.
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
        parts = platform_utils.adapt_keys(raw.split("+"))
        if parts:
            pyautogui.hotkey(*parts)
            log.info(f"Shortcut: {raw}"); stats["keystrokes"] += 1

    # ── Hotkey (browser: list of keys) ──
    elif t == "hotkey":
        keys = platform_utils.adapt_keys(data.get("keys", []))
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
            k = "+".join(platform_utils.adapt_keys(key.split("+")))
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
            ok, why = platform_utils.open_app(app, pyautogui)
            log.info(f"Open app: {app} ({'ok' if ok else why})"); stats["keystrokes"] += 1
            return {"type": "echo", "text": why, "status": "✓ Done" if ok else "✗ Failed"}

    return None


# ── Heavy command handler (system power / diagnostic cmd / health) ────────────

async def handle_heavy_cmd(t: str, data: dict):
    """
    Runs blocking work (psutil sampling, subprocess calls) in a thread pool
    so it never stalls the event loop that mouse/keyboard traffic depends on.
    """
    loop = asyncio.get_event_loop()

    if t == "system_power":
        action = data.get("action")
        if not action:
            return {"status": "error", "message": "No action specified"}
        return await loop.run_in_executor(None, execute_system_power, action)

    elif t == "system_command":
        command = data.get("command")
        if not command:
            return {"status": "error", "message": "No command specified"}
        return await loop.run_in_executor(None, execute_custom_command, command)

    elif t == "get_health":
        health = await loop.run_in_executor(None, get_pc_health)
        analysis = analyze_pc_health(health)
        return {"type": "health_report", "data": health, "analysis": analysis}

    return None


# ── Status server (localhost only — for the Electron desktop app) ─────────────
#
# Deliberately separate from the QR/web HTTPS server: bound to 127.0.0.1 only,
# so it's never reachable from the LAN like the phone-facing ports are. Just
# tells a local process (Electron) how many phones are currently connected.

def start_status_server():
    class StatusHandler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            if self.path != "/status":
                self.send_response(404)
                self.end_headers()
                return
            body = json.dumps({
                "connected": len(clients),
                "uptime_seconds": int(time.time() - stats["start_time"]),
                "stats": stats,
            }).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    try:
        with socketserver.TCPServer(("127.0.0.1", STATUS_PORT), StatusHandler) as httpd:
            log.info(f"Status feed on 127.0.0.1:{STATUS_PORT} (local only)")
            httpd.serve_forever()
    except Exception as e:
        log.warning(f"Status server failed to start: {e}")


# ── WebSocket handler ─────────────────────────────────────────────────────────

async def close_all_clients():
    for ws in list(clients):
        try:
            await ws.close(code=4401, reason="pairing reset")
        except Exception:
            pass


async def _reject(ws, reason):
    try:
        await ws.send(json.dumps({"type": "auth_failed", "reason": reason}))
        await ws.close(code=4401, reason=reason)
    except Exception:
        pass


async def serve_client(ws, secure):
    """First message must be {"type": "auth", "token": ...}; then the normal command loop runs."""
    addr = ws.remote_address
    ip = addr[0] if addr else "?"
    if not secure and not PAIRING_STORE.allow_web:
        log.info(f"Plain connection from {ip} refused (iPhone web app is switched off)")
        await _reject(ws, "web_disabled")
        return
    ok, why = False, "auth_required"
    try:
        first = json.loads(await asyncio.wait_for(ws.recv(), timeout=8))
        if isinstance(first, dict) and first.get("type") == "auth":
            ok, why = PAIRING_GUARD.check(ip, first.get("token"))
    except Exception:
        ok, why = False, "auth_required"
    if not ok:
        log.warning(f"Connection from {ip} rejected: {why}")
        await _reject(ws, why)
        return
    await ws.send(json.dumps({"type": "auth_ok"}))
    await ws_handler(ws)


async def ws_secure(ws):
    await serve_client(ws, True)


async def ws_plain(ws):
    await serve_client(ws, False)


async def ws_handler(ws):
    addr = ws.remote_address
    clients.add(ws)
    log.info(f"📱 Phone connected: {addr}")
    try:
        async for msg in ws:
            try:
                data = json.loads(msg)
                t = data.get("type", "")
                if t in HEAVY_COMMAND_TYPES:
                    reply = await handle_heavy_cmd(t, data)
                else:
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

def already_running():
    """True if another copy of VMouse already holds the connection port."""
    import socket as _socket
    probe = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
    try:
        probe.bind(("0.0.0.0", WS_PORT))
        return False
    except OSError:
        return True
    finally:
        probe.close()


def main():
    if already_running():
        message = ("VMouse seems to be running already.\n\n"
                   "Look for it on the taskbar or by the clock, or close the other copy and try again.")
        print(message)
        if os.environ.get("VMOUSE_NO_DIALOG") != "1":
            try:
                import tkinter as _tk
                from tkinter import messagebox as _mb
                _root = _tk.Tk()
                _root.withdraw()
                _mb.showinfo("VMouse", message)
                _root.destroy()
            except Exception:
                pass
        sys.exit(0)
    ip         = local_ip()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    has_ssl    = gen_cert_if_needed()

    print(f"\n{'='*50}")
    print(f"  VMouse {APP_VERSION}")
    print(f"  Powered by Bryt Ma Tech, Uganda")
    print(f"{'='*50}")
    print(f"  IP        : {ip}")
    print(f"  Secure WS : wss://{ip}:{WS_PORT}   (Android app)")
    print(f"  Web app   : http://{ip}:{HTTP_PORT}   (iPhone, same Wi-Fi)")
    scheme = "https" if has_ssl else "http"
    port   = WEB_PORT if has_ssl else 8080
    print(f"  Pairing   : scan the QR code in the window")
    print(f"{'='*50}\n")

    # Web server in background
    threading.Thread(target=start_web_server, args=(script_dir,), daemon=True).start()
    time.sleep(0.4)

    # QR popup in background - skipped when launched headless by the Electron app,
    # since the Electron window shows its own QR code instead
    if os.environ.get("VMOUSE_HEADLESS") != "1":
        threading.Thread(target=show_qr_popup, args=(ip, has_ssl), daemon=True).start()
    else:
        log.info("Headless mode (VMOUSE_HEADLESS=1) - skipping Tkinter QR popup")

    # Local-only status feed for the Electron desktop app
    threading.Thread(target=start_status_server, daemon=True).start()

    # WebSocket server (blocking)
    async def run():
        global LOOP
        LOOP = asyncio.get_running_loop()
        stop = asyncio.get_event_loop().create_future()
        signal.signal(signal.SIGINT,  lambda *_: stop.set_result(None) if not stop.done() else None)
        signal.signal(signal.SIGTERM, lambda *_: stop.set_result(None) if not stop.done() else None)
        ssl_ctx = None
        if has_ssl:
            try:
                ssl_ctx = pairing.make_server_ssl_context(VMOUSE_CERT_PATH, VMOUSE_KEY_PATH)
            except Exception as e:
                log.warning(f"Secure connection unavailable: {e}")
        async with contextlib.AsyncExitStack() as stack:
            if ssl_ctx is not None:
                await stack.enter_async_context(
                    websockets.serve(ws_secure, "0.0.0.0", WS_PORT, ssl=ssl_ctx, max_size=65536))
                log.info(f"Secure WebSocket (wss) listening on 0.0.0.0:{WS_PORT}")
            await stack.enter_async_context(
                websockets.serve(ws_plain, "0.0.0.0", WS_PLAIN_PORT, max_size=65536))
            log.info(f"Web app WebSocket (ws) listening on 0.0.0.0:{WS_PLAIN_PORT}")
            asyncio.create_task(status_loop())
            await stop
        log.info(f"Stopped. Session stats: {stats}")
    asyncio.run(run())


if __name__ == "__main__":
    main()


