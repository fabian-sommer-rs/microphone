#!/bin/bash
# Mic Button Remap - macOS Installer
# Double-click this file to install.

echo "============================================"
echo "  Mic Button Remap - Installation"
echo "============================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Check for Python 3
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] Python 3 ist nicht installiert!"
    echo ""
    echo "Installiere Python mit:"
    echo "  brew install python3"
    echo "oder lade es von https://python.org herunter."
    echo ""
    read -p "Druecke Enter zum Beenden..."
    exit 1
fi

echo "[1/3] Installiere Abhaengigkeiten..."
pip3 install pynput >/dev/null 2>&1

# Optional: tray icon
pip3 install pystray pillow >/dev/null 2>&1

echo "[2/3] Installiere MicButtonRemap..."
python3 "$SCRIPT_DIR/mic_button_remap.py" --install

echo ""
echo "[3/3] Fertig!"
echo ""
echo "============================================"
echo "  MicButtonRemap ist jetzt installiert!"
echo "  Es startet automatisch bei jedem Login."
echo ""
echo "  WICHTIG: macOS braucht Accessibility-Rechte:"
echo "  Systemeinstellungen > Datenschutz & Sicherheit"
echo "    > Bedienungshilfen"
echo "  Fuege dort Python/Terminal hinzu."
echo ""
echo "  Zum Deinstallieren:"
echo "    python3 mic_button_remap.py --uninstall"
echo "============================================"
echo ""
read -p "Druecke Enter zum Beenden..."
