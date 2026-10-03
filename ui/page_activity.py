"""VMouse activity page. Moved out of vmouse_server.py: edit this file."""
import tkinter as tk


def build(ctx):
    MUTED = ctx.MUTED
    SURFACE = ctx.SURFACE
    TEXT = ctx.TEXT
    card = ctx.card
    clients = ctx.clients
    header = ctx.header
    page = ctx.page
    stats = ctx.stats
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
    return activity_page
