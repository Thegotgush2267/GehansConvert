@echo off
setlocal enabledelayedexpansion

echo ================================
echo   SINGLE AUDIO CONVERTER
echo ================================
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
    echo No audio files found.
    pause
    exit /b
)

echo.
set /p choice=Type the number of the file you want to convert: 

set "selected=!file[%choice%]!"
set "selected_short=!file_short[%choice%]!"

if "%selected%"=="" (
    echo Invalid choice.
    pause
    exit /b
)

set /p format=Enter output format (e.g. mp3, wav, flac, aac): 

rem Get base name (without extension) from the long filename
for %%B in ("!selected!") do (
    set "basename=%%~nB"
)

echo.
echo Converting: !selected! to .%format% ...
echo.

rem Use short path for input (handles weird characters), long name for output
ffmpeg -y -i "!selected_short!" "!basename!.%format%"

echo.
echo Done.
pause
