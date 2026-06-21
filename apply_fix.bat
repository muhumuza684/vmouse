@echo off
setlocal

set SRC=%USERPROFILE%\Downloads

echo ===========================================
echo  Applying VMouse fix
echo ===========================================
echo.

if not exist lib\screens (
  echo ERROR: This doesn't look like the vmouse project folder.
  echo Run this from inside Desktop\vmouse using:
  echo   cd %%USERPROFILE%%\Desktop\vmouse
  echo   %%USERPROFILE%%\Downloads\apply_fix.bat
  pause
  exit /b 1
)

if not exist lib\services mkdir lib\services

echo Copying fixed files into place...
copy /Y "%SRC%\main.dart" lib\main.dart
copy /Y "%SRC%\qr_scan_screen.dart" lib\screens\qr_scan_screen.dart
copy /Y "%SRC%\pc_server_screen.dart" lib\screens\pc_server_screen.dart
copy /Y "%SRC%\pc_server.dart" lib\services\pc_server.dart
copy /Y "%SRC%\windows_input.dart" lib\services\windows_input.dart
copy /Y "%SRC%\AndroidManifest.xml" android\app\src\main\AndroidManifest.xml
copy /Y "%SRC%\widget_test.dart" test\widget_test.dart

echo.
echo Removing old/unused leftover files...
if exist lib\screens\mode_screen.dart del /Q lib\screens\mode_screen.dart
if exist mode_screen.dart del /Q mode_screen.dart
if exist pc_server.dart del /Q pc_server.dart
if exist pc_server_screen.dart del /Q pc_server_screen.dart
if exist windows_input.dart del /Q windows_input.dart
if exist AndroidManifest.xml del /Q AndroidManifest.xml

echo.
echo ===========================================
echo  Done. Now run these to push the fix:
echo.
echo    git add .
echo    git commit -m "Fix PC server wiring, camera permission, direct platform routing"
echo    git push
echo ===========================================
echo.
pause
