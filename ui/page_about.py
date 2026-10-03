"""VMouse about page. Moved out of vmouse_server.py: edit this file."""
import tkinter as tk
import ui_kit


def build(ctx):
    BG = ctx.BG
    BORDER = ctx.BORDER
    CORAL = ctx.CORAL
    GREEN = ctx.GREEN
    MUTED = ctx.MUTED
    PRIMARY = ctx.PRIMARY
    PRIMARY2 = ctx.PRIMARY2
    SURFACE = ctx.SURFACE
    TEXT = ctx.TEXT
    _vm_attach_scroll = ctx._vm_attach_scroll
    _vm_noop = ctx._vm_noop
    header = ctx.header
    page = ctx.page
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

        about_scrollbar = ui_kit.VMScrollbar(
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
    return about_page
