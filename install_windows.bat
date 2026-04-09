@echo off
title Mic Button Remap - Installer
echo ============================================
echo   Mic Button Remap - Installation
echo ============================================
echo.

:: Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python ist nicht installiert!
    echo.
    echo Bitte installiere Python von https://python.org
    echo WICHTIG: Setze den Haken bei "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo [1/3] Installiere Abhaengigkeiten...
pip install pynput >nul 2>&1
if errorlevel 1 (
    echo [WARN] pynput konnte nicht installiert werden, versuche pip3...
    pip3 install pynput >nul 2>&1
)

:: Optional: tray icon support
pip install pystray pillow >nul 2>&1

echo [2/3] Installiere MicButtonRemap...
python "%~dp0mic_button_remap.py" --install

echo.
echo [3/3] Fertig!
echo.
echo ============================================
echo   MicButtonRemap ist jetzt installiert!
echo   Es startet automatisch bei jedem Login.
echo.
echo   Zum Deinstallieren:
echo     python mic_button_remap.py --uninstall
echo ============================================
echo.
pause
