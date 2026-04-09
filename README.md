# Mic Button Remap

Mappt den Mute-Button deines USB-Mikrofons auf eine beliebige Aktion um - z.B. eine neue Konversation in einem Transkriptionsprogramm starten.

**Funktioniert auf Windows, macOS und Linux.**

## Schnellstart

### Option 1: Standalone Download (kein Python nötig)

1. Gehe zu [Releases](../../releases)
2. Lade die ZIP-Datei für dein System herunter
3. Entpacke und starte `MicButtonRemap`

### Option 2: Mit Python

#### Windows

1. [Python installieren](https://python.org) (Haken bei "Add to PATH" setzen!)
2. `install_windows.bat` doppelklicken
3. Fertig - startet ab jetzt automatisch bei jedem Login

#### macOS

1. Python 3 installieren: `brew install python3`
2. `install_mac.command` doppelklicken
3. Accessibility-Rechte vergeben (Systemeinstellungen > Datenschutz > Bedienungshilfen)
4. Fertig - startet ab jetzt automatisch bei jedem Login

## Konfiguration

Bearbeite `config.json`:

```json
{
    "device_name": "",
    "action_type": "keyboard_shortcut",
    "action": "ctrl+shift+n",
    "block_original": true,
    "trigger_on": "press",
    "auto_reconnect": true
}
```

| Feld | Beschreibung |
|------|-------------|
| `device_name` | Name deines Mikrofons (leer = automatisch erkennen) |
| `action_type` | `keyboard_shortcut` oder `command` |
| `action` | Der Shortcut (z.B. `ctrl+shift+n`) oder Shell-Befehl |
| `block_original` | `true` = Original-Mute wird blockiert |
| `trigger_on` | `press` oder `release` |
| `auto_reconnect` | Automatisch neu verbinden wenn USB-Gerät getrennt wird |

### Beispiele

**Tastenkombination senden:**
```json
{
    "action_type": "keyboard_shortcut",
    "action": "ctrl+shift+n"
}
```

**Programm starten:**
```json
{
    "action_type": "command",
    "action": "start https://app.example.com/new"
}
```

## Deinstallation

```bash
python mic_button_remap.py --uninstall
```

## Entwicklung

```bash
pip install -r requirements.txt
python mic_button_remap.py --run --verbose
```
