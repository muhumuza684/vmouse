"""Small UI helpers for the VMouse PC app: dark scrollbar and sidebar icons (drawn, no font needed)."""
import tkinter as tk

from PIL import Image, ImageDraw


class VMScrollbar(tk.Canvas):
    """Slim dark scrollbar that matches the app (native scrollbars ignore colors on Windows)."""

    def __init__(self, master, command=None, width=10, trough="#0B0A14", thumb="#3A3860",
                 thumb_hover="#6D5FE8", **_ignored):
        super().__init__(master, width=width, bg=trough, highlightthickness=0, bd=0)
        self._command = command
        self._thumb = thumb
        self._hover = thumb_hover
        self._first, self._last = 0.0, 1.0
        self._drag_offset = None
        self._over = False
        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<B1-Motion>", self._motion)
        self.bind("<ButtonRelease-1>", lambda e: setattr(self, "_drag_offset", None))
        self.bind("<Enter>", lambda e: self._set_over(True))
        self.bind("<Leave>", lambda e: self._set_over(False))

    def set(self, first, last):
        self._first, self._last = float(first), float(last)
        self._draw()

    def get(self):
        return self._first, self._last

    def _set_over(self, value):
        self._over = value
        self._draw()

    def _bounds(self):
        height = max(self.winfo_height(), 1)
        top = self._first * height
        bottom = max(self._last * height, top + 28)
        return top, min(bottom, height), height

    def _draw(self):
        self.delete("all")
        width = max(self.winfo_width(), 1)
        top, bottom, height = self._bounds()
        if self._last - self._first >= 0.999:
            return
        color = self._hover if (self._over or self._drag_offset is not None) else self._thumb
        pad = 2
        self.create_rectangle(pad, top + pad, width - pad, bottom - pad, fill=color, outline=color)
        # rounded ends
        r = (width - 2 * pad) / 2
        self.create_oval(pad, top + pad, width - pad, top + pad + 2 * r, fill=color, outline=color)
        self.create_oval(pad, bottom - pad - 2 * r, width - pad, bottom - pad, fill=color, outline=color)

    def _press(self, event):
        top, bottom, height = self._bounds()
        if top <= event.y <= bottom:
            self._drag_offset = event.y - top
        else:
            self._drag_offset = (bottom - top) / 2
            self._motion(event)
        self._draw()

    def _motion(self, event):
        if self._drag_offset is None or not self._command:
            return
        height = max(self.winfo_height(), 1)
        self._command("moveto", max(0.0, min(1.0, (event.y - self._drag_offset) / height)))


def nav_icon_image(name, color, size=20):
    """Line icon for the sidebar. name: connection, activity, system, products, about, support."""
    scale = 6
    s = size * scale
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    w = int(1.7 * scale)
    c = color
    u = s / 20.0

    def arc(cx, cy, r, a0, a1):
        d.arc((cx - r, cy - r, cx + r, cy + r), a0, a1, fill=c, width=w)

    if name == "connection":
        for r in (3.2 * u, 6.4 * u, 9.6 * u):
            arc(10 * u, 15 * u, r, 225, 315)
        d.ellipse((10 * u - w, 15 * u - w, 10 * u + w, 15 * u + w), fill=c)
    elif name == "activity":
        pts = [(1.5, 10), (5.5, 10), (8, 3.5), (12, 16.5), (14.5, 10), (18.5, 10)]
        d.line([(x * u, y * u) for x, y in pts], fill=c, width=w, joint="curve")
    elif name == "system":
        d.rounded_rectangle((2 * u, 3 * u, 18 * u, 13.5 * u), radius=2 * u, outline=c, width=w)
        d.line((7 * u, 17 * u, 13 * u, 17 * u), fill=c, width=w)
        d.line((10 * u, 13.5 * u, 10 * u, 17 * u), fill=c, width=w)
    elif name == "products":
        for x in (2.5, 11):
            for y in (2.5, 11):
                d.rounded_rectangle((x * u, y * u, (x + 6.5) * u, (y + 6.5) * u), radius=1.5 * u, outline=c, width=w)
    elif name == "about":
        d.ellipse((2 * u, 2 * u, 18 * u, 18 * u), outline=c, width=w)
        d.line((10 * u, 9 * u, 10 * u, 14 * u), fill=c, width=w)
        d.ellipse((10 * u - w * 0.7, 6 * u - w * 0.7, 10 * u + w * 0.7, 6 * u + w * 0.7), fill=c)
    else:  # support
        d.ellipse((2 * u, 2 * u, 18 * u, 18 * u), outline=c, width=w)
        d.ellipse((7 * u, 7 * u, 13 * u, 13 * u), outline=c, width=w)
        for a in (45, 135, 225, 315):
            d.arc((2 * u, 2 * u, 18 * u, 18 * u), a - 8, a + 8, fill=(0, 0, 0, 0), width=w + 2)
    return img.resize((size, size), Image.LANCZOS)
