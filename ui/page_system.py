"""VMouse system page. Moved out of vmouse_server.py: edit this file."""
import tkinter as tk


def build(ctx):
    MUTED = ctx.MUTED
    SURFACE = ctx.SURFACE
    TEXT = ctx.TEXT
    card = ctx.card
    header = ctx.header
    page = ctx.page
    web_url = ctx.web_url
    ws_url = ctx.ws_url
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
    return system_page
