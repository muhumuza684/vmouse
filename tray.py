"""Optional system tray icon (needs the pystray package). Does nothing if it is not installed."""
import threading


def attach(root, icon_path, quit_app, title="VMouse"):
    try:
        import pystray
        from PIL import Image
    except Exception:
        return None
    try:
        image = Image.open(icon_path)
    except Exception:
        return None
    last = {"state": "normal"}

    def track(_event=None):
        try:
            state = root.state()
            if state in ("normal", "zoomed"):
                last["state"] = state
        except Exception:
            pass

    root.bind("<Configure>", track, add="+")

    def show(_icon=None, _item=None):
        def restore():
            try:
                root.deiconify()
                if last["state"] == "zoomed":
                    root.state("zoomed")
                root.lift()
                root.focus_force()
            except Exception:
                pass
        root.after(0, restore)

    def quit_now(_icon=None, _item=None):
        try:
            icon.stop()
        except Exception:
            pass
        root.after(0, quit_app)

    menu = pystray.Menu(
        pystray.MenuItem("Open VMouse", show, default=True),
        pystray.MenuItem("Quit", quit_now),
    )
    icon = pystray.Icon("VMouse", image, title, menu)
    try:
        icon.run_detached()
    except Exception:
        threading.Thread(target=icon.run, daemon=True).start()
    return icon
