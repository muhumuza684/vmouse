; Inno Setup script for the VMouse Windows installer.
; Build with:  iscc installer\VMouse.iss   (after python build_app.py)
#define AppName "VMouse"
#define AppVersion GetEnv("VMOUSE_VERSION")
#if AppVersion == ""
  #define AppVersion "1.0.0"
#endif

[Setup]
AppId={{6E1F4F0A-5B7B-4C1E-9E65-2B0D7F8A3C11}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Bryt Ma Tech Uganda
DefaultDirName={autopf}\VMouse
DefaultGroupName=VMouse
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=VMouse-Setup-{#AppVersion}
SetupIconFile=..\assets\vmouse.ico
UninstallDisplayIcon={app}\VMouse.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64compatible

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"
Name: "startup"; Description: "Start VMouse when I sign in to Windows"; GroupDescription: "Startup:"; Flags: unchecked

[Files]
Source: "..\dist\VMouse.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\VMouse"; Filename: "{app}\VMouse.exe"
Name: "{autodesktop}\VMouse"; Filename: "{app}\VMouse.exe"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "VMouse"; ValueData: """{app}\VMouse.exe"""; Flags: uninsdeletevalue; Tasks: startup

[Run]
Filename: "{app}\VMouse.exe"; Description: "Start VMouse now"; Flags: nowait postinstall skipifsilent
