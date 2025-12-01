@echo off
echo.
echo ===============================
echo      FFmpeg Installer
echo ===============================
echo.

:: Check if winget exists
where winget >nul 2>&1
if %errorlevel% neq 0 (
    echo Winget not found on this system.
    echo You need Windows 10/11 with App Installer installed.
    pause
    exit /b
)

echo Installing FFmpeg (Gyan build)...
echo.

:: Install FFmpeg Gyan exact ID
winget install --id Gyan.FFmpeg -e --source winget

if %errorlevel% neq 0 (
    echo.
    echo Something went wrong during installation.
    pause
    exit /b
)

echo.
echo FFmpeg installation complete, homie.
echo Type "ffmpeg -version" to check.
echo.
pause
