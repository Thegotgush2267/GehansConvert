@echo off
setlocal enabledelayedexpansion


echo ================================
echo   FFmpeg Check / Installer
echo ================================
echo.

:: Check if ffmpeg is already installed (in PATH)
where ffmpeg >nul 2>&1
if %errorlevel%==0 (
    echo FFmpeg is already installed.
    goto :converter
)

echo FFmpeg not found. Trying to install via winget...
echo.

:: Check if winget exists
where winget >nul 2>&1
if %errorlevel% neq 0 (
    echo winget is not available on this system.
    echo Install FFmpeg manually and run this script again.
    goto :end
)

:: Try installing FFmpeg (Gyan build) via winget
winget install --id Gyan.FFmpeg -e --source winget

echo.
echo Verifying FFmpeg installation...
where ffmpeg >nul 2>&1
if %errorlevel%==0 (
    echo FFmpeg is installed.
) else (
    echo Could not install FFmpeg automatically.
    echo Please install FFmpeg manually and then re-run this script.
    goto :end
)

:: ==========================
::   CONVERTER SECTION
:: ==========================
:converter
echo.
echo ==========================================
echo   Welcome To The Audio Converter By Gehans
echo ==========================================
echo.

echo Available audio files:
echo -----------------------
set count=0
for %%A in (*.mp3 *.wav *.aac *.m4a *.ogg *.flac *.wma *.webm) do (
    set /a count+=1
    echo !count!: %%A
    rem Store long name
    set "file[!count!]=%%A"
    rem Store short (8.3) path for ffmpeg
    set "file_short[!count!]=%%~sfA"
)

if %count%==0 (
    echo No audio files found in this folder.
    goto :end
)

echo.
set /p choice=Type the number of the file you want to convert: 

set "selected=!file[%choice%]!"
set "selected_short=!file_short[%choice%]!"

if "%selected%"=="" (
    echo Invalid choice.
    goto :end
)

set /p format=Enter output format (e.g. mp3, wav, flac, aac): 
echo Please do not choose a video format.
echo Please do not choose the same format as the input file.

:: Get base name (without extension) from the long filename
for %%B in ("!selected!") do (
    set "basename=%%~nB"
)

cls

echo.
echo Converting: !selected! to .%format% ...
echo.

:: Use ffmpeg from PATH
ffmpeg -y -i "!selected_short!" "!basename!.%format%"

cls

echo.
echo Done.
goto :end

:end
echo.
pause
endlocal

