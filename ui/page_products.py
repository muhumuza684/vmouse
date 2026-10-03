"""VMouse products page. Moved out of vmouse_server.py: edit this file."""
from PIL import Image, ImageTk
import os
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
    SURFACE2 = ctx.SURFACE2
    TEXT = ctx.TEXT
    _vm_attach_scroll = ctx._vm_attach_scroll
    _vm_noop = ctx._vm_noop
    base_dir = ctx.base_dir
    header = ctx.header
    page = ctx.page
    root = ctx.root
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

        products_scrollbar = ui_kit.VMScrollbar(
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
                                os.path.abspath(ctx.app_file)
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
    return products_page
