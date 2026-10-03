# Releasing VMouse

Everything is built on GitHub. You do not need to build anything on your own PC.

## Make a release

1. Update the version in `pubspec.yaml` (`version: 1.0.0+1`) and `APP_VERSION` in `vmouse_server.py`.
2. Commit and push.
3. Create the release tag:

       git tag v1.0.0
       git push origin v1.0.0

4. Open the **Actions** tab. When the run turns green, the **Releases** page has:
   - `VMouse-Setup-1.0.0.exe` (Windows installer), `VMouse.exe` (portable)
   - `VMouse-1.0.0-linux.tar.gz`, `VMouse-1.0.0-mac.zip`
   - `VMouse.apk` (Android)

## Sign the Android app (recommended)

An APK signed with the debug key shows extra Android warnings. Create one private key, once:

    keytool -genkey -v -keystore release.keystore -alias vmouse -keyalg RSA -keysize 2048 -validity 10000

Keep `release.keystore` and its passwords safe and **never put them in the repository**. Then add four
secrets under Settings, Secrets and variables, Actions: `ANDROID_KEYSTORE_BASE64`
(the keystore converted with `certutil -encode` or `base64`), `ANDROID_KEYSTORE_PASSWORD`,
`ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD`.

## Security warnings people will see

- **Windows SmartScreen** warns about programs without a paid code-signing certificate. Users click
  "More info", then "Run anyway". A certificate removes the warning.
- **Mac** shows a warning for apps not signed by Apple. Users right-click the app, choose Open.
- **Linux** needs no signing. Run `chmod +x VMouse` after extracting.
