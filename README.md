# VMouse

Use your phone as a mouse, keyboard and remote for your computer.
Built by Bryt Ma Tech Uganda.

## Download

Get the latest version from the **Releases** page of this repository:

| For | File |
| --- | --- |
| Windows PC | `VMouse-Setup-x.y.z.exe` (installer) or `VMouse.exe` (portable) |
| Mac | `VMouse-x.y.z-mac.zip` |
| Linux | `VMouse-x.y.z-linux.tar.gz` |
| Android phone | `VMouse.apk` |
| iPhone | no download: scan the QR code with the camera |

## How it works

1. Run VMouse on your computer. It shows a QR code.
2. Android: open the VMouse app and scan the code. iPhone: scan it with the camera and open the link.
3. Control your computer with the trackpad, keyboard, shortcuts, system controls and health monitor.

Your phone and computer must be on the same Wi-Fi network. Only phones that scanned your QR code can
connect. Use **Reset pairing** in VMouse to cut off every phone and make a new code.

On Windows, if your phone cannot connect, press **Fix connection** in VMouse to allow it through the firewall.

## Security

- A secret pairing code in the QR code is required for every connection.
- The Android app connects over TLS and checks your computer's certificate fingerprint.
- The iPhone web app cannot trust a home-made certificate, so it connects without encryption but still needs the
  pairing code. You can switch it off in VMouse.

## Build from source

PC app (Python 3.10 or newer):

    pip install -r requirements.txt
    python vmouse_server.py
    python build_app.py        # builds the program for your system into dist/

Android app: `flutter pub get`, then `flutter build apk --release`.

Releases are built by GitHub. See [RELEASING.md](RELEASING.md).

## Built with

Python, Tkinter, WebSockets and PyAutoGUI for the PC app. Flutter for the Android app. A small web app for iPhone.
