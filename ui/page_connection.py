"""VMouse connection page. Moved out of vmouse_server.py: edit this file."""
from PIL import Image, ImageTk
import asyncio, json, logging, os, signal, socket, sys, time, threading, ssl
import pairing
import platform_utils
import tkinter as tk
import ui_kit


def build(ctx):
    BG = ctx.BG
    BORDER = ctx.BORDER
    GREEN = ctx.GREEN
    LOOP = ctx.LOOP
    MUTED = ctx.MUTED
    PAIRING_STORE = ctx.PAIRING_STORE
    PRIMARY = ctx.PRIMARY
    PRIMARY2 = ctx.PRIMARY2
    RED = ctx.RED
    SURFACE = ctx.SURFACE
    SURFACE2 = ctx.SURFACE2
    TEXT = ctx.TEXT
    _vm_attach_scroll = ctx._vm_attach_scroll
    card = ctx.card
    clients = ctx.clients
    close_all_clients = ctx.close_all_clients
    header = ctx.header
    ip = ctx.ip
    make_qr_image = ctx.make_qr_image
    page = ctx.page
    root = ctx.root
    ws_url = ctx.ws_url
    show_page = ctx.show_page
    def connection_page():

        header(
            "Connect your phone",
            "The PC displays the QR code. Your phone scans it to connect."
        )

        shell = tk.Frame(page, bg=BG)
        shell.pack(fill="both", expand=True)
        body_canvas = tk.Canvas(shell, bg=BG, highlightthickness=0, bd=0)
        body_scroll = ui_kit.VMScrollbar(shell, orient="vertical", command=body_canvas.yview)
        body_canvas.configure(yscrollcommand=body_scroll.set)
        body_scroll.pack(side="right", fill="y")
        body_canvas.pack(side="left", fill="both", expand=True)
        body = tk.Frame(body_canvas, bg=BG)
        body_window = body_canvas.create_window((0, 0), window=body, anchor="nw")
        _vm_attach_scroll(body_canvas, body, body_window)
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

        qr_photo = ImageTk.PhotoImage(make_qr_image())

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

        # -- Connection type, pairing and troubleshooting ---------------
        tools = tk.Frame(right, bg=SURFACE)
        tools.pack(fill="x", padx=22, pady=(16, 0))
        tk.Label(tools, text="CONNECTION TYPE", font=("Segoe UI", 9, "bold"), bg=SURFACE, fg=MUTED).pack(anchor="w")
        seg = tk.Frame(tools, bg=SURFACE2)
        seg.pack(fill="x", pady=(6, 0))
        tk.Label(seg, text="Wi-Fi", font=("Segoe UI", 10, "bold"), bg=PRIMARY, fg="white", padx=16, pady=7).pack(side="left", padx=4, pady=4)
        tk.Label(seg, text="Bluetooth (coming soon)", font=("Segoe UI", 10), bg=SURFACE2, fg=MUTED, padx=12, pady=7).pack(side="left", padx=4, pady=4)
        net_hint = pairing.network_hint(ip) or platform_utils.startup_notice() or ""
        if net_hint:
            tk.Label(tools, text=net_hint, font=("Segoe UI", 9), bg=SURFACE, fg=RED, anchor="w", justify="left", wraplength=320).pack(fill="x", pady=(8, 0))
        web_var = tk.BooleanVar(value=PAIRING_STORE.allow_web)

        def toggle_web():
            PAIRING_STORE.set_allow_web(web_var.get())

        tk.Checkbutton(
            tools, text="Allow iPhone web app (not encrypted)", variable=web_var, command=toggle_web,
            bg=SURFACE, fg=TEXT, selectcolor=SURFACE2, activebackground=SURFACE, activeforeground=TEXT,
            font=("Segoe UI", 9), bd=0, highlightthickness=0, cursor="hand2"
        ).pack(anchor="w", pady=(10, 0))
        btn_row = tk.Frame(tools, bg=SURFACE)
        btn_row.pack(fill="x", pady=(10, 0))
        tool_note = tk.Label(tools, text="", font=("Segoe UI", 9), bg=SURFACE, fg=MUTED, anchor="w", justify="left", wraplength=320)

        def do_reset():
            PAIRING_STORE.reset()
            if LOOP is not None:
                asyncio.run_coroutine_threadsafe(close_all_clients(), LOOP)
            try:
                fresh = ImageTk.PhotoImage(make_qr_image())
                qr_label.config(image=fresh)
                qr_label.image = fresh
            except Exception:
                pass
            tool_note.config(text="Pairing reset. Phones must scan the new code.", fg=GREEN)

        def do_firewall():
            ok, msg = pairing.open_firewall()
            tool_note.config(text=msg, fg=GREEN if ok else RED)

        for label_text, action in (("Reset pairing", do_reset), ("Fix connection", do_firewall)):
            tk.Button(
                btn_row, text=label_text, command=action, font=("Segoe UI", 9, "bold"), bg=SURFACE2, fg=TEXT,
                activebackground=BORDER, activeforeground=TEXT, bd=0, padx=12, pady=7, cursor="hand2"
            ).pack(side="left", padx=(0, 8))
        tool_note.pack(fill="x", pady=(8, 0))
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
            ("02", "Scan the QR", "Android app or iPhone camera."),
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
    return connection_page
