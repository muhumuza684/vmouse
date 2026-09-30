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

STATUS_PORT  = 8764  # localhost-only JSON status feed for the Electron desktop app
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
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]; s.close(); return ip
    except:
        return "127.0.0.1"


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



def start_web_server(directory):
    has_ssl = gen_cert_if_needed()
    os.chdir(directory)
    handler = http.server.SimpleHTTPRequestHandler
    handler.log_message = lambda *a: None

    if has_ssl:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(str(VMOUSE_CERT_PATH), str(VMOUSE_KEY_PATH))
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
        from PIL import Image, ImageTk
        import qrcode as qc
        import webbrowser
        import sys
        import os

        scheme = "https" if has_ssl else "http"
        port = WEB_PORT if has_ssl else 8080

        web_url = f"{scheme}://{ip}:{port}"
        ws_url = f"ws://{ip}:{WS_PORT}"

        # ----------------------------------------------------
        # QR displayed BY THE PC.
        # The phone scans this.
        # ----------------------------------------------------
        qr = qc.QRCode(
            border=2,
            error_correction=qc.constants.ERROR_CORRECT_M
        )

        qr.add_data(ws_url)
        qr.make(fit=True)

        qr_img = qr.make_image(
            fill_color="#12111F",
            back_color="white"
        ).convert("RGB")

        qr_img = qr_img.resize(
            (300, 300),
            Image.NEAREST
        )

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
        def connection_page():

            header(
                "Connect your phone",
                "The PC displays the QR code. Your phone scans it to connect."
            )

            body = tk.Frame(
                page,
                bg=BG
            )

            body.pack(
                fill="both",
                expand=True
            )

            body.grid_columnconfigure(0, weight=3)
            body.grid_columnconfigure(1, weight=2)

            # QR CARD
            left = card(body)

            left.grid(
                row=0,
                column=0,
                sticky="nsew",
                padx=(0, 12)
            )

            tk.Label(
                left,
                text="SCAN THIS QR CODE",
                font=("Segoe UI", 11, "bold"),
                bg=SURFACE,
                fg=PRIMARY2
            ).pack(
                pady=(24, 5)
            )

            tk.Label(
                left,
                text="Open VMouse on your phone and scan this code.",
                font=("Segoe UI", 10),
                bg=SURFACE,
                fg=MUTED
            ).pack()

            qr_photo = ImageTk.PhotoImage(qr_img)

            qr_label = tk.Label(
                left,
                image=qr_photo,
                bg="white"
            )

            qr_label.image = qr_photo

            qr_label.pack(
                pady=18
            )

            tk.Label(
                left,
                text="PC CONNECTION",
                font=("Segoe UI", 8, "bold"),
                bg=SURFACE,
                fg=MUTED
            ).pack()

            tk.Label(
                left,
                text=ws_url,
                font=("Consolas", 11),
                bg=SURFACE,
                fg=PRIMARY2
            ).pack(
                pady=(3, 22)
            )

            # RIGHT CARD
            right = card(body)

            right.grid(
                row=0,
                column=1,
                sticky="nsew",
                padx=(12, 0)
            )

            tk.Label(
                right,
                text="CONNECTION STATUS",
                font=("Segoe UI", 9, "bold"),
                bg=SURFACE,
                fg=MUTED
            ).pack(
                anchor="w",
                padx=22,
                pady=(24, 8)
            )

            status = tk.Label(
                right,
                text="Waiting for phone",
                font=("Segoe UI", 12, "bold"),
                bg="#07070D", fg=RED,
                anchor="w",
                padx=14,
                pady=12
            )

            status.pack(
                fill="x",
                padx=22
            )

            tk.Label(
                right,
                text="HOW IT WORKS",
                font=("Segoe UI", 9, "bold"),
                bg=SURFACE,
                fg=MUTED
            ).pack(
                anchor="w",
                padx=22,
                pady=(28, 10)
            )

            steps = [
                ("01", "Install VMouse", "Install the VMouse mobile app."),
                ("02", "Scan the QR", "Use the phone camera inside VMouse."),
                ("03", "Control your PC", "Use the trackpad, keyboard and controls.")
            ]

            for number, title, description in steps:

                row = tk.Frame(
                    right,
                    bg=SURFACE
                )

                row.pack(
                    fill="x",
                    padx=22,
                    pady=6
                )

                tk.Label(
                    row,
                    text=number,
                    bg=PRIMARY,
                    fg="white",
                    font=("Segoe UI", 9, "bold"),
                    padx=8,
                    pady=4
                ).pack(side="left")

                txt = tk.Frame(
                    row,
                    bg=SURFACE
                )

                txt.pack(
                    side="left",
                    padx=10
                )

                tk.Label(
                    txt,
                    text=title,
                    font=("Segoe UI", 10, "bold"),
                    bg=SURFACE,
                    fg=TEXT
                ).pack(anchor="w")

                tk.Label(
                    txt,
                    text=description,
                    font=("Segoe UI", 8),
                    bg=SURFACE,
                    fg=MUTED
                ).pack(anchor="w")

            # PRODUCT ADVERTISEMENT
            advertisement = tk.Frame(
                right,
                bg="#1F1F2B",
                highlightbackground="#2A2940",
                highlightthickness=1
            )

            advertisement.pack(
                fill="x",
                padx=22,
                pady=(25, 12)
            )

            tk.Label(
                advertisement,
                text="MORE FROM BRYT MA TECH",
                font=("Segoe UI", 8, "bold"),
                bg="#1F1F2B",
                fg="#A79EF5"
            ).pack(
                anchor="w",
                padx=14,
                pady=(12, 3)
            )

            tk.Label(
                advertisement,
                text="AI / Websites / BI / Software",
                font=("Segoe UI", 12, "bold"),
                bg="#1F1F2B",
                fg="white"
            ).pack(
                anchor="w",
                padx=14
            )

            tk.Label(
                advertisement,
                text="Explore our products and custom technology services.",
                font=("Segoe UI", 8),
                bg="#1F1F2B",
                fg="#F7FBF3"
            ).pack(
                anchor="w",
                padx=14,
                pady=(2, 10)
            )

            tk.Button(
                advertisement,
                text="Explore Other Products →",
                command=lambda: show_page("products"),
                bg=PRIMARY,
                fg="white",
                activebackground="#8378F0", activeforeground="white",
                bd=0,
                padx=12,
                pady=7,
                font=("Segoe UI", 9, "bold"),
                cursor="hand2"
            ).pack(
                anchor="w",
                padx=14,
                pady=(0, 14)
            )

            # ----------------------------------------------------
            # Safe connection-status timer
            # ----------------------------------------------------
            status_timer = {"id": None, "active": True}

            def stop_status_timer():

                status_timer["active"] = False

                timer_id = status_timer.get("id")

                if timer_id is not None:

                    try:
                        root.after_cancel(timer_id)
                    except Exception:
                        pass

                    status_timer["id"] = None

            def update_status():

                if not status_timer["active"]:
                    return

                try:

                    if not root.winfo_exists():
                        stop_status_timer()
                        return

                    if not status.winfo_exists():
                        stop_status_timer()
                        return

                    count = len(clients)

                    if count:

                        status.config(
                            text=f"{count} phone{'s' if count != 1 else ''} connected",
                            fg=GREEN
                        )

                    else:

                        status.config(
                            text="Waiting for phone",
                            fg=RED
                        )

                    status_timer["id"] = root.after(
                        1000,
                        update_status
                    )

                except tk.TclError:

                    stop_status_timer()

                except Exception:

                    stop_status_timer()

            root.protocol(
                "WM_DELETE_WINDOW",
                lambda: (
                    stop_status_timer(),
                    root.destroy()
                )
            )

            root.after(
                300,
                update_status
            )

        # ----------------------------------------------------
        # OTHER PAGES
        # ----------------------------------------------------
        def activity_page():

            header(
                "Activity",
                "Live information about the current VMouse session."
            )

            c = card(page)
            c.pack(fill="x")

            values = [
                ("Connected phones", lambda: len(clients)),
                ("Mouse movements", lambda: stats.get("moves", 0)),
                ("Clicks", lambda: stats.get("clicks", 0)),
                ("Keystrokes", lambda: stats.get("keystrokes", 0))
            ]

            for label, value in values:

                row = tk.Frame(
                    c,
                    bg=SURFACE
                )

                row.pack(
                    fill="x",
                    padx=24,
                    pady=12
                )

                tk.Label(
                    row,
                    text=label,
                    font=("Segoe UI", 10),
                    bg=SURFACE,
                    fg=MUTED
                ).pack(side="left")

                tk.Label(
                    row,
                    text=str(value()),
                    font=("Segoe UI", 11, "bold"),
                    bg=SURFACE,
                    fg=TEXT
                ).pack(side="right")

        def system_page():

            header(
                "System & Health",
                "PC host information and VMouse service status."
            )

            c = card(page)
            c.pack(fill="x")

            data = [
                ("VMouse host", "Running"),
                ("WebSocket", ws_url),
                ("Web interface", web_url),
                ("Platform", "Windows PC"),
                ("Status", "Ready for phone connection")
            ]

            for key, value in data:

                row = tk.Frame(
                    c,
                    bg=SURFACE
                )

                row.pack(
                    fill="x",
                    padx=24,
                    pady=12
                )

                tk.Label(
                    row,
                    text=key,
                    font=("Segoe UI", 10),
                    bg=SURFACE,
                    fg=MUTED
                ).pack(side="left")

                tk.Label(
                    row,
                    text=value,
                    font=("Segoe UI", 10, "bold"),
                    bg=SURFACE,
                    fg=TEXT
                ).pack(side="right")


        def products_page():
            # VMOUSE_09B_PRODUCTS_REBUILD

            # ------------------------------------------------------------
            # PRODUCTS PAGE
            # ------------------------------------------------------------

            # Remove any previous page contents.
            for child in page.winfo_children():
                child.destroy()

            # Header remains part of the existing VMouse layout.
            header(
                "Other Products",
                "Technology products and services from Bryt Ma Tech Uganda."
            )

            # ------------------------------------------------------------
            # OUTER SCROLL CONTAINER
            # ------------------------------------------------------------

            products_shell = tk.Frame(
                page,
                bg=BG,
            )

            products_shell.pack(
                fill="both",
                expand=True,
                padx=24,
                pady=(4, 18),
            )

            products_canvas = tk.Canvas(
                products_shell,
                bg=BG,
                highlightthickness=0,
                bd=0,
                relief="flat",
            )

            products_scrollbar = tk.Scrollbar(
                products_shell,
                orient="vertical",
                command=products_canvas.yview,
                width=11,
                bg=PRIMARY,
                activebackground=PRIMARY2,
                troughcolor=SURFACE,
                relief="flat",
                bd=0,
                highlightthickness=0,
            )

            products_canvas.configure(
                yscrollcommand=products_scrollbar.set
            )

            products_scrollbar.pack(
                side="right",
                fill="y",
                padx=(8, 0),
            )

            products_canvas.pack(
                side="left",
                fill="both",
                expand=True,
            )

            products_content = tk.Frame(
                products_canvas,
                bg=BG,
            )

            products_window = products_canvas.create_window(
                (0, 0),
                window=products_content,
                anchor="nw",
            )


            def _products_update_scrollregion(event=None):
                products_canvas.configure(
                    scrollregion=products_canvas.bbox("all")
                )


            def _products_resize_content(event):
                products_canvas.itemconfigure(
                    products_window,
                    width=event.width,
                )


            products_content.bind(
                "<Configure>",
                _products_update_scrollregion,
            )

            products_canvas.bind("<Configure>", _products_resize_content,)
            _vm_attach_scroll(products_canvas, products_content, products_window)

            # ------------------------------------------------------------
            # RELIABLE WINDOWS MOUSE WHEEL
            # ------------------------------------------------------------

            def _products_mousewheel(event):
                try:
                    if not products_canvas.winfo_exists():
                        return

                    if event.delta:
                        movement = -int(event.delta / 120)

                        if movement == 0:
                            movement = -1 if event.delta > 0 else 1

                        products_canvas.yview_scroll(
                            movement,
                            "units",
                        )
                except Exception:
                    pass


            def _products_linux_wheel(event):
                try:
                    if not products_canvas.winfo_exists():
                        return

                    products_canvas.yview_scroll(
                        -1 if event.num == 4 else 1,
                        "units",
                    )
                except Exception:
                    pass


            def _products_enable_wheel(event=None):
                try:
                    _vm_noop(
                        "<MouseWheel>",
                        _products_mousewheel,
                    )

                    _vm_noop(
                        "<Button-4>",
                        _products_linux_wheel,
                    )

                    _vm_noop(
                        "<Button-5>",
                        _products_linux_wheel,
                    )
                except Exception:
                    pass


            def _products_disable_wheel(event=None):
                try:
                    _vm_noop(
                        "<MouseWheel>"
                    )

                    _vm_noop(
                        "<Button-4>"
                    )

                    _vm_noop(
                        "<Button-5>"
                    )
                except Exception:
                    pass


            products_canvas.bind(
                "<Enter>",
                _products_enable_wheel,
            )

            products_canvas.bind(
                "<Leave>",
                _products_disable_wheel,
            )

            # Also enable wheel while pointer is inside the content.
            products_content.bind(
                "<Enter>",
                _products_enable_wheel,
            )

            products_content.bind(
                "<Leave>",
                _products_disable_wheel,
            )

            # Clean global bindings when this canvas is destroyed.
            products_canvas.bind(
                "<Destroy>",
                _products_disable_wheel,
            )

            # ------------------------------------------------------------
            # VISUAL SECTION BUILDER
            # ------------------------------------------------------------

            _VMOUSE_PRODUCT_ICONS = {
                "Apps": "product_app.png",
                "Books": "product_books.png",
                "Business Intelligence": "product_bi.png",
                "APIs": "product_api.png",
                "MCP Servers": "product_mcp.png",
            }
            if not hasattr(root, "_vmouse_prod_icons"):
                root._vmouse_prod_icons = []

            def _product_section(number, label, title, description, items, accent):
                outer = tk.Frame(products_content, bg=BORDER, bd=0, highlightthickness=0)
                outer.pack(fill="x", pady=(0, 14))
                card = tk.Frame(outer, bg=SURFACE, bd=0, highlightthickness=0)
                card.pack(fill="both", expand=True, padx=1, pady=1)
                tk.Frame(card, bg=accent, width=7).pack(side="left", fill="y")
                body = tk.Frame(card, bg=SURFACE)
                body.pack(fill="both", expand=True, padx=24, pady=22)

                left = tk.Frame(body, bg=SURFACE)
                left.pack(side="left", anchor="n", padx=(0, 26))
                photo = None
                icon_name = _VMOUSE_PRODUCT_ICONS.get(label)
                if icon_name:
                    try:
                        img = Image.open(os.path.join(base_dir, "assets", icon_name)).convert("RGBA").resize((116, 116), Image.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        root._vmouse_prod_icons.append(photo)
                    except Exception:
                        photo = None
                if photo is not None:
                    tk.Label(left, image=photo, bg=SURFACE, bd=0).pack()
                else:
                    tile = tk.Frame(left, bg=accent, width=116, height=116)
                    tile.pack_propagate(False)
                    tile.pack()
                    tk.Label(tile, text=f"{number:02d}", font=("Segoe UI", 30, "bold"), fg=BG, bg=accent).pack(expand=True)

                right = tk.Frame(body, bg=SURFACE)
                right.pack(side="left", fill="both", expand=True)
                top = tk.Frame(right, bg=SURFACE)
                top.pack(fill="x")
                tk.Label(top, text=f"{number:02d}", font=("Segoe UI", 10, "bold"), fg=BG, bg=accent, width=4, pady=4).pack(side="left")
                tk.Label(top, text=label.upper(), font=("Segoe UI", 9, "bold"), fg=accent, bg=SURFACE).pack(side="left", padx=(11, 0))
                title_lbl = tk.Label(right, text=title, font=("Segoe UI", 19, "bold"), fg=TEXT, bg=SURFACE, anchor="w", justify="left")
                title_lbl.pack(fill="x", pady=(9, 0))
                desc = tk.Label(right, text=description, font=("Segoe UI", 10), fg=MUTED, bg=SURFACE, anchor="w", justify="left", wraplength=560)
                desc.pack(fill="x", pady=(7, 13))
                grid = tk.Frame(right, bg=SURFACE)
                grid.pack(fill="x")
                grid.grid_columnconfigure(0, weight=1, uniform="col")
                grid.grid_columnconfigure(1, weight=1, uniform="col")
                cells = []
                for item in items:
                    cell = tk.Frame(grid, bg=SURFACE2)
                    tk.Frame(cell, bg=accent, width=4).pack(side="left", fill="y")
                    tk.Label(cell, text="●", font=("Segoe UI", 8, "bold"), fg=accent, bg=SURFACE2).pack(side="left", padx=(11, 7), pady=8)
                    lbl = tk.Label(cell, text=item, font=("Segoe UI", 10), fg=TEXT, bg=SURFACE2, anchor="w", justify="left", wraplength=260)
                    lbl.pack(side="left", fill="x", expand=True, padx=(0, 12), pady=8)
                    cell.bind("<Configure>", lambda e, l=lbl: l.config(wraplength=max(120, e.width - 52)))
                    cells.append(cell)
                state = {"cols": 0}

                def _layout(e=None):
                    width = right.winfo_width()
                    if width <= 1:
                        return
                    desc.config(wraplength=max(200, width - 8))
                    title_lbl.config(wraplength=max(200, width - 8))
                    cols = 2 if width >= 560 else 1
                    if cols == state["cols"]:
                        return
                    state["cols"] = cols
                    grid.grid_columnconfigure(0, weight=1, uniform="col" if cols == 2 else "")
                    grid.grid_columnconfigure(1, weight=1 if cols == 2 else 0, uniform="col" if cols == 2 else "")
                    for j, c in enumerate(cells):
                        c.grid(row=j // cols, column=j % cols, sticky="ew", padx=((0, 6) if j % 2 == 0 else (6, 0)) if cols == 2 else 0, pady=3)

                right.bind("<Configure>", _layout)
                _layout()
                tk.Frame(card, bg=accent, height=3).pack(fill="x", side="bottom")
            # ------------------------------------------------------------
            # APPLICATIONS
            # ------------------------------------------------------------

            _product_section(
                1,
                "Apps",
                "Applications & Digital Systems",
                "Software products and digital systems developed by Bryt Ma Tech Uganda.",
                [
                    "Revive Data",
                    "VMouse",
                    "Bryt Ma VPN",
                    "Mantoni Data Cleaning Pipeline",
                    "E-Suggestion Box",
                    "E-Present / E-Rollcall System",
                    "Kolla",
                    "Power BI Visuals",
                    "Teddy Operating System",
                    "Atwooki Code",
                    "Eagle App",
                    "Custom Sandbox by Bryt Ma",
                ],
                PRIMARY,
            )

            # ------------------------------------------------------------
            # BOOKS
            # ------------------------------------------------------------

            _product_section(
                2,
                "Books",
                "Bryt Ma Books",
                "Stories, lessons and ideas designed to inspire faith, character and positive impact.",
                [
                    "GOD OF BALIMWEZO — Faith • Humility • Obedience",
                    "CARRY ME — Love • Support • Impact",
                    "SOMEONE BETTER — There is always someone better than you",
                    "REJECTIONS IN MONACO — Accepting and dealing with rejection",
                    "SHE DA MOON — Many women, but one is like a moon among many stars for each man",
                    "BLIND ON PURPOSE",
                ],
                PRIMARY2,
            )

            # ------------------------------------------------------------
            # BUSINESS INTELLIGENCE
            # ------------------------------------------------------------

            _product_section(
                3,
                "Business Intelligence",
                "BI, Data & Power BI",
                "Dashboards, data analysis, reporting and custom Power BI visual development.",
                [
                    "Monthly Performance — line graph reporting",
                    "Service Performance — bar graph reporting",
                    "Data analysis and decision-support dashboards",
                    "Custom Power BI visuals and BI solutions",
                ],
                GREEN,
            )

            # ------------------------------------------------------------
            # APIS
            # ------------------------------------------------------------

            _product_section(
                4,
                "APIs",
                "API Development & Integrations",
                "Practical APIs and integrations for modern software systems.",
                [
                    "OpenAI API",
                    "GitHub API",
                    "Stripe API",
                    "Google Maps API",
                    "Twilio API",
                ],
                CORAL,
            )

            # ------------------------------------------------------------
            # MCP
            # ------------------------------------------------------------

            _product_section(
                5,
                "MCP Servers",
                "Model Context Protocol Servers",
                "Tools and integrations that connect AI systems to useful data and services.",
                [
                    "Filesystem MCP Server",
                    "Git MCP Server",
                    "GitHub MCP Server",
                    "PostgreSQL MCP Server",
                    "Google Drive MCP Server",
                ],
                PRIMARY,
            )

            # ------------------------------------------------------------
            # WEBSITES
            # ------------------------------------------------------------

            _product_section(
                6,
                "Websites",
                "Websites & Digital Presence",
                "Modern, responsive websites for businesses, organizations and personal brands.",
                [
                    "Business websites",
                    "Organization and NGO websites",
                    "Landing pages and product pages",
                    "Deployment and domain setup",
                ],
                PRIMARY2,
            )

            # ------------------------------------------------------------
            # SOFTWARE DEVELOPMENT
            # ------------------------------------------------------------

            _product_section(
                7,
                "Software Development",
                "Custom Software Development",
                "Practical software built around real business, education and operational needs.",
                [
                    "Web applications",
                    "Desktop applications",
                    "Mobile applications",
                    "Business and educational systems",
                    "AI-enabled software solutions",
                ],
                GREEN,
            )

            # Footer.
            tk.Frame(
                products_content,
                bg=PRIMARY,
                height=2,
            ).pack(
                fill="x",
                pady=(3, 10),
            )

            tk.Label(
                products_content,
                text="Bryt Ma Tech Uganda  •  Build practical technology. Create real impact.",
                font=("Segoe UI", 9, "bold"),
                fg=MUTED,
                bg=BG,
            ).pack(
                pady=(0, 28),
            )

            products_content.update_idletasks()

            products_canvas.configure(
                scrollregion=products_canvas.bbox("all")
            )

            

            # VMOUSE_09C_ROBUST_RUNTIME
            #
            # Products-page runtime wiring.
            # Uses real Tk widget discovery instead of guessed variable names.


            def _vmouse_products_all_children(widget):
                """Return all descendant Tk widgets recursively."""

                found = []

                try:
                    children = widget.winfo_children()
                except Exception:
                    return found

                for child in children:

                    found.append(child)

                    found.extend(
                        _vmouse_products_all_children(child)
                    )

                return found


            def _vmouse_products_find_canvas():
                """
                Find the currently mapped Products canvas.

                We intentionally do not assume a variable name such as
                products_canvas, canvas, or product_canvas.
                """

                try:

                    widgets = _vmouse_products_all_children(root)

                    candidates = []

                    for widget in widgets:

                        try:

                            if not isinstance(
                                widget,
                                tk.Canvas
                            ):
                                continue

                            if not widget.winfo_ismapped():
                                continue

                            scrollregion = widget.cget(
                                "scrollregion"
                            )

                            if not scrollregion:
                                continue

                            candidates.append(widget)

                        except Exception:
                            continue

                    if not candidates:
                        return None

                    # Prefer the largest mapped scrollable canvas.
                    candidates.sort(
                        key=lambda item: (
                            item.winfo_width()
                            * item.winfo_height()
                        ),
                        reverse=True
                    )

                    return candidates[0]

                except Exception:
                    return None


            def _vmouse_products_find_label(
                category
            ):
                """
                Find a visible Tk Label whose displayed text
                corresponds to a Products category.
                """

                try:

                    widgets = _vmouse_products_all_children(root)

                    target = category.strip().lower()

                    for widget in widgets:

                        try:

                            if not isinstance(
                                widget,
                                tk.Label
                            ):
                                continue

                            if not widget.winfo_ismapped():
                                continue

                            text_value = str(
                                widget.cget("text")
                            ).strip()

                            if not text_value:
                                continue

                            normalized = text_value.lower()

                            if normalized == target:
                                return widget

                            # Also allow headings such as:
                            #
                            # "Apps — Applications & Digital Systems"
                            #
                            if normalized.startswith(
                                target + " "
                            ):
                                return widget

                            if normalized.startswith(
                                target + "—"
                            ):
                                return widget

                            if normalized.startswith(
                                target + " -"
                            ):
                                return widget

                        except Exception:
                            continue

                except Exception:
                    pass

                return None


            def _vmouse_products_attach_icons():
                """
                Attach the real category PNGs directly to the
                existing category heading labels.

                This does not rebuild the Products layout.
                """

                try:

                    return
                    icon_assets = {
                        "Apps": "product_app.png",
                        "Books": "product_books.png",
                        "Business Intelligence": "product_bi.png",
                        "APIs": "product_api.png",
                        "MCP Servers": "product_mcp.png",
                    }

                    # Keep references alive.
                    if not hasattr(
                        root,
                        "_vmouse_products_icon_refs"
                    ):
                        root._vmouse_products_icon_refs = {}

                    for category, filename in icon_assets.items():

                        try:

                            label = _vmouse_products_find_label(
                                category
                            )

                            if label is None:
                                continue

                            asset_path = os.path.join(
                                os.path.dirname(
                                    os.path.abspath(__file__)
                                ),
                                "assets",
                                filename
                            )

                            if not os.path.exists(
                                asset_path
                            ):
                                continue

                            icon_image = Image.open(
                                asset_path
                            ).convert("RGBA")

                            icon_image.thumbnail(
                                (58, 58),
                                Image.LANCZOS
                            )

                            icon_photo = ImageTk.PhotoImage(
                                icon_image
                            )

                            root._vmouse_products_icon_refs[
                                category
                            ] = icon_photo

                            label.configure(
                                image=icon_photo,
                                compound="left"
                            )

                            label.image = icon_photo

                        except Exception:
                            continue

                except Exception:
                    pass


            def _vmouse_products_refresh_scroll():
                """
                Refresh the actual Products canvas scrollregion.
                """

                try:

                    canvas = _vmouse_products_find_canvas()

                    if canvas is None:
                        return

                    canvas.update_idletasks()

                    bbox = canvas.bbox("all")

                    if bbox:
                        canvas.configure(
                            scrollregion=bbox
                        )

                except Exception:
                    pass


            def _vmouse_products_mousewheel(event):
                """
                Windows mouse-wheel handler.
                """

                try:

                    canvas = _vmouse_products_find_canvas()

                    if canvas is None:
                        return

                    delta = getattr(
                        event,
                        "delta",
                        0
                    )

                    if delta == 0:
                        return

                    amount = int(
                        -delta / 120
                    )

                    if amount == 0:
                        amount = (
                            -1
                            if delta > 0
                            else 1
                        )

                    canvas.yview_scroll(
                        amount,
                        "units"
                    )

                except Exception:
                    pass


            def _vmouse_products_wheel_up(event):
                try:

                    canvas = _vmouse_products_find_canvas()

                    if canvas is not None:
                        canvas.yview_scroll(
                            -3,
                            "units"
                        )

                except Exception:
                    pass


            def _vmouse_products_wheel_down(event):
                try:

                    canvas = _vmouse_products_find_canvas()

                    if canvas is not None:
                        canvas.yview_scroll(
                            3,
                            "units"
                        )

                except Exception:
                    pass


            # ======================================================================
            # INSTALL GLOBAL WHEEL BINDINGS ONLY ONCE
            # ======================================================================

            try:

                if not getattr(
                    root,
                    "_vmouse_09c_wheel_bound",
                    False
                ):

                    _vm_noop("<x>", _vmouse_products_mousewheel,
                        add="+"
                    )

                    _vm_noop("<x>", _vmouse_products_wheel_up,
                        add="+"
                    )

                    _vm_noop("<x>", _vmouse_products_wheel_down,
                        add="+"
                    )

                    root._vmouse_09c_wheel_bound = True

            except Exception:
                pass


            # ======================================================================
            # RUN AFTER TK HAS FINISHED BUILDING THE PRODUCTS WIDGETS
            # ======================================================================

            try:

                root.after(
                    80,
                    _vmouse_products_attach_icons
                )

                root.after(
                    100,
                    _vmouse_products_refresh_scroll
                )

                root.after(
                    300,
                    _vmouse_products_attach_icons
                )

                root.after(
                    350,
                    _vmouse_products_refresh_scroll
                )

            except Exception:
                pass



        def about_page():

            # VMOUSE_09B_ABOUT_REBUILD

            # ------------------------------------------------------------
            # ABOUT PAGE
            # ------------------------------------------------------------

            for child in page.winfo_children():
                child.destroy()

            header(
                "About VMouse",
                "Simple remote control for your PC, built by Bryt Ma Tech Uganda."
            )

            # ------------------------------------------------------------
            # ABOUT OUTER SCROLL AREA
            # ------------------------------------------------------------

            about_shell = tk.Frame(
                page,
                bg=BG,
            )

            about_shell.pack(
                fill="both",
                expand=True,
                padx=24,
                pady=(4, 18),
            )

            about_canvas = tk.Canvas(
                about_shell,
                bg=BG,
                highlightthickness=0,
                bd=0,
                relief="flat",
            )

            about_scrollbar = tk.Scrollbar(
                about_shell,
                orient="vertical",
                command=about_canvas.yview,
                width=11,
                bg=PRIMARY,
                activebackground=PRIMARY2,
                troughcolor=SURFACE,
                relief="flat",
                bd=0,
                highlightthickness=0,
            )

            about_canvas.configure(
                yscrollcommand=about_scrollbar.set
            )

            about_scrollbar.pack(
                side="right",
                fill="y",
                padx=(8, 0),
            )

            about_canvas.pack(
                side="left",
                fill="both",
                expand=True,
            )

            about_content = tk.Frame(
                about_canvas,
                bg=BG,
            )

            about_window = about_canvas.create_window(
                (0, 0),
                window=about_content,
                anchor="nw",
            )


            def _about_scrollregion(event=None):
                about_canvas.configure(
                    scrollregion=about_canvas.bbox("all")
                )


            def _about_width(event):
                about_canvas.itemconfigure(
                    about_window,
                    width=event.width,
                )


            about_content.bind(
                "<Configure>",
                _about_scrollregion,
            )

            about_canvas.bind("<Configure>", _about_width,)
            _vm_attach_scroll(about_canvas, about_content, about_window)


            def _about_wheel(event):
                try:
                    if not about_canvas.winfo_exists():
                        return

                    movement = -int(event.delta / 120)

                    if movement == 0:
                        movement = -1 if event.delta > 0 else 1

                    about_canvas.yview_scroll(
                        movement,
                        "units",
                    )
                except Exception:
                    pass


            def _about_linux_wheel(event):
                try:
                    if not about_canvas.winfo_exists():
                        return

                    about_canvas.yview_scroll(
                        -1 if event.num == 4 else 1,
                        "units",
                    )
                except Exception:
                    pass


            def _about_enable_wheel(event=None):
                try:
                    _vm_noop(
                        "<MouseWheel>",
                        _about_wheel,
                    )

                    _vm_noop(
                        "<Button-4>",
                        _about_linux_wheel,
                    )

                    _vm_noop(
                        "<Button-5>",
                        _about_linux_wheel,
                    )
                except Exception:
                    pass


            def _about_disable_wheel(event=None):
                try:
                    _vm_noop(
                        "<MouseWheel>"
                    )

                    _vm_noop(
                        "<Button-4>"
                    )

                    _vm_noop(
                        "<Button-5>"
                    )
                except Exception:
                    pass


            about_canvas.bind(
                "<Enter>",
                _about_enable_wheel,
            )

            about_canvas.bind(
                "<Leave>",
                _about_disable_wheel,
            )

            about_content.bind(
                "<Enter>",
                _about_enable_wheel,
            )

            about_content.bind(
                "<Leave>",
                _about_disable_wheel,
            )

            about_canvas.bind(
                "<Destroy>",
                _about_disable_wheel,
            )

            # ------------------------------------------------------------
            # HERO
            # ------------------------------------------------------------

            hero_outer = tk.Frame(
                about_content,
                bg=PRIMARY,
            )

            hero_outer.pack(
                fill="x",
                pady=(0, 15),
            )

            hero = tk.Frame(
                hero_outer,
                bg=SURFACE,
            )

            hero.pack(
                fill="both",
                expand=True,
                padx=(5, 0),
            )

            tk.Frame(
                hero,
                bg=CORAL,
                height=5,
            ).pack(
                fill="x",
            )

            hero_body = tk.Frame(
                hero,
                bg=SURFACE,
            )

            hero_body.pack(
                fill="x",
                padx=24,
                pady=22,
            )

            tk.Label(
                hero_body,
                text="VMOUSE",
                font=("Segoe UI", 11, "bold"),
                fg=PRIMARY2,
                bg=SURFACE,
            ).pack(
                anchor="w",
            )

            tk.Label(
                hero_body,
                text="Cross-platform PC remote control",
                font=("Segoe UI", 24, "bold"),
                fg=TEXT,
                bg=SURFACE,
            ).pack(
                anchor="w",
                pady=(4, 0),
            )

            tk.Label(
                hero_body,
                text="Version 1.0.0   •   Made in Uganda   •   © Bryt Ma Tech Uganda",
                font=("Segoe UI", 10),
                fg=MUTED,
                bg=SURFACE,
            ).pack(
                anchor="w",
                pady=(9, 0),
            )

            # ------------------------------------------------------------
            # ABOUT CARD BUILDER
            # ------------------------------------------------------------

            def _about_section(
                number,
                heading,
                description,
                accent,
            ):

                outer = tk.Frame(
                    about_content,
                    bg=BORDER,
                )

                outer.pack(
                    fill="x",
                    pady=(0, 14),
                )

                card = tk.Frame(
                    outer,
                    bg=SURFACE,
                )

                card.pack(
                    fill="both",
                    expand=True,
                    padx=1,
                    pady=1,
                )

                # Strong edge.
                tk.Frame(
                    card,
                    bg=accent,
                    width=7,
                ).pack(
                    side="left",
                    fill="y",
                )

                body = tk.Frame(
                    card,
                    bg=SURFACE,
                )

                body.pack(
                    fill="both",
                    expand=True,
                    padx=22,
                    pady=19,
                )

                top = tk.Frame(
                    body,
                    bg=SURFACE,
                )

                top.pack(
                    fill="x",
                )

                tk.Label(
                    top,
                    text=f"{number:02d}",
                    font=("Segoe UI", 9, "bold"),
                    fg=BG,
                    bg=accent,
                    width=4,
                    pady=4,
                ).pack(
                    side="left",
                )

                tk.Label(
                    top,
                    text=heading,
                    font=("Segoe UI", 18, "bold"),
                    fg=TEXT,
                    bg=SURFACE,
                ).pack(
                    side="left",
                    padx=(12, 0),
                )

                _about_desc = tk.Label(body, text=description, font=("Segoe UI", 10), fg=MUTED, bg=SURFACE, justify="left", anchor="w", wraplength=700)
                _about_desc.pack(fill="x", pady=(11, 0))
                body.bind("<Configure>", lambda e, _l=_about_desc: _l.config(wraplength=max(200, e.width - 8)))

                tk.Frame(
                    card,
                    bg=accent,
                    height=2,
                ).pack(
                    fill="x",
                    side="bottom",
                )


            _about_section(
                1,
                "Technology Stack",
                "Python — Windows host/server and desktop control logic\n"
                "Tkinter — VMouse Windows desktop interface\n"
                "PyAutoGUI — keyboard and mouse control\n"
                "WebSockets — real-time PC control communication\n"
                "HTTPS/TLS — secure web transport and certificate support\n"
                "Flutter / Dart — Android and web client technology\n"
                "PyInstaller — Windows executable packaging",
                PRIMARY,
            )

            _about_section(
                2,
                "Why VMouse Was Built",
                "VMouse was built to provide a simple way to control a Windows PC "
                "from another device on the same network. The project brings desktop "
                "software, mobile technology and real-time communication together "
                "in one practical tool, while providing a foundation for future "
                "cross-platform remote-control support.",
                CORAL,
            )

            _about_section(
                3,
                "Built by Bryt Ma Tech Uganda",
                "VMouse is part of a wider technology portfolio focused on practical "
                "software, AI, data, websites, APIs, business intelligence and "
                "digital products designed for real-world use.",
                GREEN,
            )

            _about_section(
                4,
                "Product Direction",
                "The project is designed to grow from a Windows host into a broader "
                "cross-platform remote-control system, with Android and web access "
                "and future Linux support.",
                PRIMARY2,
            )

            # ------------------------------------------------------------
            # FOOTER
            # ------------------------------------------------------------

            tk.Frame(
                about_content,
                bg=PRIMARY,
                height=2,
            ).pack(
                fill="x",
                pady=(4, 10),
            )

            tk.Label(
                about_content,
                text="Made in Uganda  •  Bryt Ma Tech Uganda",
                font=("Segoe UI", 9, "bold"),
                fg=MUTED,
                bg=BG,
            ).pack(
                pady=(0, 24),
            )

            about_content.update_idletasks()

            about_canvas.configure(
                scrollregion=about_canvas.bbox("all")
            )

        def support_page():

            header(
                "Support",
                "Need help connecting VMouse?"
            )

            c = card(page)
            c.pack(fill="x")

            tk.Label(
                c,
                text="muhumuzabright26@gmail.com",
                font=("Segoe UI", 11),
                bg=SURFACE,
                fg=PRIMARY2
            ).pack(
                anchor="w",
                padx=28,
                pady=(28, 6)
            )

            tk.Button(
                c,
                text="Email Support",
                command=lambda: webbrowser.open(
                    "mailto:muhumuzabright26@gmail.com"
                ),
                bg=PRIMARY,
                fg="white",
                bd=0,
                padx=16,
                pady=8,
                font=("Segoe UI", 9, "bold"),
                cursor="hand2"
            ).pack(
                anchor="w",
                padx=28,
                pady=8
            )

            tk.Label(
                c,
                text="WhatsApp: +256 759 621 612",
                font=("Segoe UI", 10),
                bg=SURFACE,
                fg=MUTED
            ).pack(
                anchor="w",
                padx=28,
                pady=(8, 4)
            )

            tk.Button(
                c,
                text="WhatsApp Support",
                command=lambda: webbrowser.open(
                    "https://wa.me/256759621612"
                ),
                bg="#2A2940", fg="white",
                bd=0,
                padx=16,
                pady=8,
                font=("Segoe UI", 9, "bold"),
                cursor="hand2"
            ).pack(
                anchor="w",
                padx=28,
                pady=(4, 28)
            )

        def nav_button(label, page_name, symbol):

            button = tk.Button(
                sidebar,
                text=f"  {symbol}   {label}",
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
                button.config(
                    bg=SIDEBAR,
                    fg=MUTED
                )

            nav_buttons[name].config(
                bg="#1F1F2B",
                fg=TEXT
            )

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


