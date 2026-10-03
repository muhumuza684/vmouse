"""VMouse support page. Moved out of vmouse_server.py: edit this file."""
import tkinter as tk
import webbrowser


def build(ctx):
    MUTED = ctx.MUTED
    PRIMARY = ctx.PRIMARY
    PRIMARY2 = ctx.PRIMARY2
    SURFACE = ctx.SURFACE
    card = ctx.card
    header = ctx.header
    page = ctx.page
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
    return support_page
