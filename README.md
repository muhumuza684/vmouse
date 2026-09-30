# VMouse

Use your phone as a mouse, keyboard and remote for your Windows PC.
Built by Bryt Ma Tech Uganda.

## How it works

1. Run VMouse on your PC. It shows a QR code.
2. Open the VMouse app on your phone and scan the code.
3. Control your PC with the trackpad, keyboard, shortcuts, system controls and health monitor.

Your phone and PC must be on the same Wi-Fi network.

## Status

| Platform | State |
| --- | --- |
| Windows PC app | Available |
| Android phone app | Available |
| iPhone (web app) | Planned |
| Linux and Mac PC app | Planned |

## Build from source

Windows PC app:

    pip install -r requirements.txt
    python vmouse_server.py
    python build_exe.py        # builds dist/VMouse.exe

Android app:

    flutter pub get
    flutter build apk --release

## Built with

Python, Tkinter, WebSockets and PyAutoGUI for the PC app. Flutter and Dart for the phone app.

## Support

Use the Support page inside the app.
