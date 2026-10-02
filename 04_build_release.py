"""VMouse script 04: build and release. One build script for Windows, Mac and Linux, a Windows installer,
GitHub builds that publish a release when you push a tag, Android release signing, a new README.
Run from the repo folder:  python 04_build_release.py   (after scripts 01 to 03)
Aborts without changes if anything expected is missing."""
import base64, os, re, shutil, sys, zlib

def _payload(b64):
    return zlib.decompress(base64.b64decode(b64))

def read_text(path):
    raw = open(path, 'rb').read().decode('utf-8')
    nl = '\r\n' if '\r\n' in raw else '\n'
    return raw.replace('\r\n', '\n'), nl

def write_text(path, text, nl='\n'):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    open(path, 'wb').write(text.replace('\n', nl).encode('utf-8'))

def write_payload(path, b64):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    open(path, 'wb').write(_payload(b64))

def flex(t):
    return r'\s*'.join(re.escape(x) for x in re.findall(r'[(),]|[^\s(),]+', t))

class Patcher:
    def __init__(self, path):
        self.path = path
        self.text, self.nl = read_text(path)
        self.n = 0
    def sub(self, old, new, count=1, regex=False):
        pat = old if regex else flex(old)
        text, k = re.subn(pat, lambda m: new, self.text)
        if k != count:
            sys.exit(f'ABORTED, nothing changed. Expected {count} match(es) in {self.path} for {old[:70]!r}, found {k}')
        self.text = text
        self.n += k
    def has(self, s):
        return s in self.text
    def save(self):
        write_text(self.path, self.text, self.nl)

def need(path, what):
    if not os.path.exists(path):
        sys.exit(f'ABORTED: {path} not found. {what}')

def backup(path, tag):
    dest = os.path.join('..', f'{os.path.basename(path)}_before_{tag}')
    shutil.copy(path, dest)
    return dest

PAYLOAD = {
    'build_app.py': (
        'eNqlVltPIzcUfp9f4fplZ0riha0qVVSpxELaIgFBCdpty6aWM+Mhbmbsqe0hCYj/3uPLhAkFdaUiAbbPxefync+DMf7YiqpAny5V'
        'azgqlUZ2yZHZGstrtFUtYpojJVH6WchCrc0AXbIcgdqFkO0mI0mC4KfZ2iUoLZwvypqGNNskmXLTVvYYFcLY9+ECwjd85yob9EUo'
        'DR6d774FeEMp3AlXYYwTUTdKW6RMt9K8W5lla0W127WLRqucm50mJJWUWtWoYXZZiQWK59ewhWgnkxs08puU0lJUnNKMaG5Udc/T'
        'jDRQCGmT8dXN9HfQ8+rvEb6vXZTUcH3PNaSNk5PZbHwz66kwY7g1OLn+fNI7bdYMJ+enEziKFjtvROQKJ8mv52dn4yuQ3/oaY7sS'
        '0nKNBwhfn1/Ef+S8Znd8b3Oz2tueabZ2B3/rXBX8eUWEk5JGVHgQLljzhVH5ygULWpOGy9nM39MYV1m/2rLWqrtWhI2xmm0784YJ'
        'LeSdk4AnaiyzIne7VtCVsG4V1BFeclbZJV0yWVQho4C4/klTMQt4rKm7GyJK5sn1xcnNz5PpJd2V5jFGLuR3H/Axuu1iIjQczWNs'
        'BdNwsK8RzzqVysFvX2OjtE/nN0CL03tKkqTgJdKtTHNV1xBsdhwGADK3Kf7JaSNM/lJCpuAkzTM/UzkSEnUWmbfQ3LZa9mBKclZV'
        '6e0bVvMBytfFyKEni1HAZFAAnRFKpjEMq7dh4Td8Y6FEHrEAZFZQd5JyCd2HPo1wa8vhDzjbGcSQNCeGM50vU/3u5PqafhpPZ+eT'
        'qy/m2xH84vT2Tzw/yPC7gb8hI3datU16FPzwTc4bi8b+H0R2/NI7PiKH5BDHHGq24lTk0nQZwIw7goEJkCAsgJLcxDpOiqzhRcRR'
        'gVP3UoB6N8se8aEUTN9x2xs4T07YrSKzuGtxTzeOOKlXhdAp3wAJUbUa3eiWh9y8c6JgLlIY3IxAIFB/aPv0l48n2JOFeOBp+v3R'
        'hwGCP0BwweTi5Or0j8ksI4YBl4Tb9lAQjnY1EbuGOhhIzgteOCykvpfg9XQyQI5OIBmoCt+Qpa0rnD0XW5RIKhtNic9lV+JdQ5gA'
        '2p35wRtvhE1LPJ5OJ9Nj9BjtNIcZFPecWpV65D15r6VqZUEicLoxhUrDDJNu62WGN3CMf8QunmfFUTewiFcQAT4OXYhId4TnPMFT'
        'kbeWLSoOMzWsPadtzyXQShUZYjiUCnpQCl2HbV5xJqOE1Z7rQq8jRfV+QIUVxbBgloFaiR8DCT89QsxPkbEH/9aCogcVR9/zJJb6'
        'ldSeS92ldQB5gT8luXtcgvO1xzQvws4hG/vuBs+8eum7o7G3nL/qrzdj/liZzXDROp4digIAL0oR6gnOyEJvbc0sz5ckPEa4i8Xw'
        '/8xp/oxZKL9DbCTqA/SCugnAPY2U268ggfZqa9YCXuEozgJKOo0Bup1nb0ayFAWkNAxsADm5OOZ9dLnvCS6LMElZlADNjPZIvWus'
        'F30zQoc9Gns5NU4nGEQyBl971Oxl7pOmR0Zui78KPqp1dt78mbpgNvDXQuRVBxAg3mmEDyficeJ4HybeP17RpoxGw8eY0tOwZjl2'
        'YHoQDQ5fcYM919krmHktjv8TQ0QHXHz3AKB5GUdHT/5hLvEX6T50LXqEMJ4QSrte7fxl2L2rUE1KHWgo9dWk1LExpbGegZqTfwDZ'
        'lWW+'
    ),
    'installer/VMouse.iss': (
        'eNqNU0tv2zgQvvNXDJRLe7ARd9O0a0MHP1tjkSawkvSwDgpGGkmEZVLLh101yH/vUKJjF9kt9kbO45tv5psZwVJKBQlaV4NJtagt'
        '5EqDLRHur5QzCF+FzNTegJDG8qpC3WcjmDhRZbAXthwCCJOmR/e6y+sLYwDgDc8taqgbWyoJjz7tG6/rft28ZWcZ5kIijOv6C98i'
        'RF1mdOq4R20EZX5CO5e7NxRyfZfMv93PV8ny+ktEICI/jYtjiCIG8C8Q0aB/3j8ndJSZyBn7u+36gVHIMoufni7ng8XF4nzcez/5'
        'MOldTAfz3p/zy/e9d5Pz2YfFx/Ef08HgmQWy8dNZeLWmUKOzhk/ruHGPlTAl6niiGwtXHG4xLeGu4DLjbIY5d5WdCd1hcmdVnT+H'
        'ER7cn7RyXdGDXRj+WOGNVoXm29Z9wwuMGzTs2tnaecS4319nwthgmXCDC1GhPOL02gH0fuXc2papkj7YY3Bj0Jr1btupmip2J4PY'
        'xKOueOOjiXtdH4j38TuyqdrWGk07lurHlr9jiapEdmr2fL+KH1xniW2o2lZlqCW70WJHxQs0K/zHCY1ZXKk9UiuvPdc71FpkaMaV'
        'j8niTPBKFWys01JYTK2jYsuO7lJeXkyEvaIq8ffLi5SYcCtokLQLt9xszAPzUx5CRHgbUoKaldEIZthdBlEm31QjtwgcQhCYUmmb'
        'OkuRrRS/hifBa4bRAZ3IaBryK+TE2w9nty9RwhKMKCTdFlh1OMT/KNNhDsm7qHhhhuBkWmK6wYy681pSd4lyOvUMwmqcyNWR8XtD'
        '7lbLIxJRUBp33YYQmtf7OKunwrM5SO+zwpYdgE6rvCT5TQ8D/J+pI2g1GsKJOERmhQV1opsHtlLKDuHzX9O7ESTucYONn4vK7Z5r'
        'XF+JVCtDv3WY43rqtEZpw+avV85rfc8rh7dNTRQIVcgimALvF6atccYtJ2P0mmx0qgNdS4YVWtz5pJc+whr4Hpx8YL/v/TebItX+'
        'WI0+XFiolbHhSMFsRC1y4+Et+wmZqRjX'
    ),
    '.github/workflows/build.yml': (
        'eNrtV21v2zYQ/p5fcTC6OAlCuXGzdHDQIW6TAkHTJIiLBcNcGJRE26xlUuWLE/flv+9ISbYk20k3FN0G7Itsks+98Tkej4JOWQde'
        'Wp7E8NtbaTXb2pKiswWQWj12vwChoiIaM92BP2BKuYD3ftrQkZ9qzvaafiq1STJQ7KNl2jjJO6kmw0TeDWKuU2oiVLeVMjXlWnMp'
        'tINEUhgmDOq5U9yg7Q8y9Asm1wEgvIfvcKz9WFmhCboINrTCWJJQh/VL2rBUZ1IABDAYVEwj46y1MIJoIq05mR1uQGhmbErSuRlL'
        'cTL7OUdhHNyMO4sRxukRZMaUi6MDzWfBQbu5UJo5fC60oUmyEEO3O/ClrIWnwDOQ04gx4I9MmdAaJ7Q1PIE7FmoZTVge+lL7jRV+'
        'i/Rm/XyI3JA4g8H7YzBjJnLfgUwLm+RjhjgGlmgGLBpLaFzKXGwok5gpmDPTOIYh33KschHLO10m5zabgh12z4CKuIiLqd0qZbks'
        'aT9tt//bjBEFLtO5YlOXv4G5Nxu5XexGzWD51AW4dVXLOVOhAw1omgbpfK18Xfsax5HTSC4c4kJIv3FA5kCIkCRVcqSY1iWRbWi8'
        '6vSv3QKdwmueMKT3/pej3f45ikPPyx/1z3uvXjnXG0s3+nlAXOsNrNk0kTQmVBk+xLklvavEZYFmGkmePeV9pgivhAqAxca01mxq'
        'bY34EMiexyAo4cLel5P6wk2srTjtdvD08F+Xvr05eoPHmkYTOmK1wqBtLIGmhoyYAZvGWDNhe7s6vUjteW7wGTGTxd/7hIegIyXN'
        'Dz82RfzOhXVH4NvPzffJw2SRGeUsLOfWXoYJDFXB6JNLrymNZKVmvqVRNbk8ghwc/l8X/xFSpzkfmylFRPCJp45NvOOU5HGZz242'
        'Bd3rNz+kTflAZ/Sh4JzviofWeGKxMljFRWndyZeIP3jerJnTNpSaG9kaJtYYpkhm/2TW3mizQJbzqf08OGxW7iIqBEtwDckPE7Yh'
        '2yBm2ArFTES8XstyK9huhoB1qybfjWPMwIRRbGY0HwkuRjBhc9iRIpm7pmguLTIgFYtBCra70M3ErBzLm7Pfe++ubs4GL7u9s6PD'
        'Djz5/Bk0ixQ2Y0H38vTm6vx0UAPB16/rNFx3e73bq5vTR3QUsBUtg+7Febe3UTpbXpV61Oxaixv6SAGNJ7VoG0VTWbliswZyFfsF'
        'QqQE9whb0l+LA9TCo9zK2QqQJc9LRV2KWWuG0PAr11RrfFTEL37SfYHw+ribcKr9wMNd1/Kirr0vGmX3ii3IJ1fGfm8bJY9RT4D9'
        'Er5jTDkzl6Hf1JKPCZfmcaMEdZ32GknsussZmyVpx22xqyp42vBYhJliTF53+PxazELrJcomsFdf1ywWJ6OoUiuHyldYbAkm2Bnm'
        '4JqiS/wWPlV1RGkm7lnFEpZao5fVI524+UJp4EzkXRr+/c7FPCdrpaCXDOJa7kq5il/bMOF6DOXQ+RCLId7kRt+izZ0RfmwYKDbc'
        'hyZ+dcs9hFuzZlZKBGOxfxa7cr9fvHj2s/5yP7vl94tsyl/Sf/euQM3imzco24ECWX9QXuB1gUmTrBRb9H8pBMTMUwbD+lUhh8ad'
        'Cd3KPCOjccHzQ9fFiAmmMNRBjh0IaZw6oyyrpHLiZqtd/sKlVvVxsK67/wtyj+M9j629orV7EItkI9L1DA/CitJSys4/AaCeMX0='
    ),
    'RELEASING.md': (
        'eNplVE1v2zgQvetXDJJL4lpE0gaLRW7axtgGaWrDahv0ZNLUWCIikQRJ2VF+/Q4p2U26vtgeznvz9WbOYY0tCq90DT8fTe8xyxZ7'
        'dENookl52PaqDWA0/KvCl37L4JfpoTKgTQCNWEEwyacCoScUOQ+md2AOGlafWZadn8OjeEYQ4FI0CnLN4IetREAIDQJF9IpgSgO3'
        '/dZblGwQXcvhgk9vt3DNrtjVh2t+SZEq4MVqtfm5WJf3y288AfddzH/j0RGE2YGz7CODz6brVEgQ2/uGZZ/I5vAYeUoIgqhvswzG'
        'T00AMsA+hXxrjRRgnKop4PSa3TBYWtSJbjYrZKBs/WxGDNStp2Z6cT199057qB2ink/uY/sx+ltRIzTC38aAOfBxHnmJobd5isXw'
        'BaklT0pX5uCpaB9E26K7nB+9Jw9rHEVv8fI9VSLJW6X7FxaEY/Urn//x2AnJXpXl74BM2GdiLXTljKou00BLVY+FTVYQ1sKFQ0n9'
        'Rl1hdCs0FKsH8ORKQjmo0CREhdu+hmccwDexDnwJTpx4DsJpUpE/jcloBOvUPv4m0JwMEqdh0f9gTAt5jToS5nvI6dsH406zZSdD'
        'LlolPIxCSY6irWFdFiNIvSJ8vLr5m1jIsVJhgOsr+mTZA6IF/icfT6pSwdPovD8YV3nwYofJPJtpJB2SYkIsuosSHQVnjVcEH2Yz'
        'Bt+jPERVwY4WJvMoHRJdT/1zQIMPsRFz+jXaI+9eOBVHS+ZJare0C9/u1sv7u83D4lf5fblebP4pysVfNzy7iCFP9UujKaVwnAWX'
        '9KcPitqHWpqKCjIO+JZqJGwU1f94V0VZPi3Xd3yevX3cFF/vi5K/R/x2Hk8AVdG72NTjhMGisS1SMm0LHukq5NS2o7rLTrhQyrgs'
        'tBwRQw3YGmqndaZ2ovOpimgQNABSTiwhj2KLRyjWpnZKkmro1NBR8CBbJZ9JNmePsRlK78xZWkMNZ2vaTrpfBzGcMSjegmlgndmj'
        'T8ObMmcp0UchKbFRwuL4RIN0cRV8OpCT8rcDFJYqPSZC96MJeUon0ZL/HGRjDKkynpKR/2vcU4oQr2ykg6k0BjFbLpvOVPDhZbrb'
        'JMZdINWkZZIhZfkf9M3yZw=='
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
need('vmouse_server.py', 'Run this inside the vmouse repo folder.')
need('pairing.py', 'Run 01_security_connection.py and 02_iphone_pwa.py first.')
need('pwa/index.html', 'Run 02_iphone_pwa.py first (the build bundles the web app).')

if os.path.exists('build_app.py') and os.path.exists('installer/VMouse.iss'):
    sys.exit('Already applied. Nothing to do.')

# 1. One cross-platform build script replaces build_exe.py
write_payload('build_app.py', PAYLOAD['build_app.py'])
if os.path.exists('build_exe.py'):
    os.remove('build_exe.py')
    print('Removed build_exe.py (build_app.py replaces it: Windows, Mac and Linux)')

# 2. Windows installer, GitHub build and release, release guide
write_payload('installer/VMouse.iss', PAYLOAD['installer/VMouse.iss'])
write_payload('.github/workflows/build.yml', PAYLOAD['.github/workflows/build.yml'])
write_payload('RELEASING.md', PAYLOAD['RELEASING.md'])
print('Wrote installer/VMouse.iss, .github/workflows/build.yml and RELEASING.md')

# 3. Android release signing (reads android/key.properties if it exists, otherwise the debug key)
g = 'android/app/build.gradle'
need(g, 'The Android project is missing.')
gp = Patcher(g)
if 'keystoreProperties' not in gp.text:
    gp.sub('android {', '''def keystoreProperties = new Properties()
def keystorePropertiesFile = rootProject.file("key.properties")
if (keystorePropertiesFile.exists()) {
    keystorePropertiesFile.withReader("UTF-8") { reader -> keystoreProperties.load(reader) }
}

android {''')
    gp.sub('buildTypes {', '''signingConfigs {
        release {
            if (keystorePropertiesFile.exists()) {
                keyAlias keystoreProperties["keyAlias"]
                keyPassword keystoreProperties["keyPassword"]
                storeFile file(keystoreProperties["storeFile"])
                storePassword keystoreProperties["storePassword"]
            }
        }
    }

    buildTypes {''')
    gp.sub('signingConfig = signingConfigs.debug', 'signingConfig = keystorePropertiesFile.exists() ? signingConfigs.release : signingConfigs.debug')
    gp.save()
    print('Android release signing is ready (add the key as GitHub secrets, see RELEASING.md)')

# 4. Keep keys out of git
gi = open('.gitignore', encoding='utf-8').read() if os.path.exists('.gitignore') else ''
add = [r for r in ['android/key.properties', '*.keystore', '*.jks', 'dist/', 'build/'] if r not in gi.split()]
if add:
    open('.gitignore', 'a', encoding='utf-8', newline='\n').write('\n' + '\n'.join(add) + '\n')
    print('Added to .gitignore:', ', '.join(add))

# 5. README for the finished product
write_text('README.md', '''# VMouse

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
''')
print('Wrote the new README.md')
print('\nDone. Test the build with: python build_app.py')
