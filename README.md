# Mic Button Remap

Mappt den Mute-Button deines USB-Mikrofons auf den **"Neue Konsultation"**-Button in [app.curala](https://app.curala).

**Funktioniert auf Windows und macOS.**

## So funktioniert es

```
[Mute-Button am Mikrofon] --> [Python-Script] --> [Browser-Extension] --> [Klick auf "Neue Konsultation"]
```

Das Python-Script erkennt den Mute-Button und sendet ein Signal an die Browser-Extension. Die Extension klickt dann automatisch den "Neue Konsultation"-Button in app.curala.

## Installation

### Schritt 1: Script installieren

#### Windows
1. [Python installieren](https://python.org) (Haken bei **"Add to PATH"** setzen!)
2. `install_windows.bat` doppelklicken
3. Fertig - startet ab jetzt automatisch bei jedem Login

#### macOS
1. Python 3 installieren: `brew install python3`
2. `install_mac.command` doppelklicken
3. Accessibility-Rechte vergeben (Systemeinstellungen > Datenschutz > Bedienungshilfen)
4. Fertig - startet ab jetzt automatisch bei jedem Login

### Schritt 2: Browser-Extension installieren

#### Chrome / Edge
1. Gehe zu `chrome://extensions` (Chrome) oder `edge://extensions` (Edge)
2. Aktiviere **"Entwicklermodus"** (Schalter oben rechts)
3. Klicke **"Entpackte Erweiterung laden"**
4. Wähle den `extension/` Ordner aus diesem Projekt
5. Fertig!

Die Extension ist jetzt aktiv und wartet auf Signale vom Python-Script.

## Konfiguration

Bearbeite `config.json`:

```json
{
    "device_name": "",
    "action_type": "browser_extension",
    "trigger_port": 59213,
    "block_original": true,
    "trigger_on": "press",
    "auto_reconnect": true
}
```

| Feld | Beschreibung |
|------|-------------|
| `device_name` | Name deines Mikrofons (leer = automatisch erkennen) |
| `action_type` | `browser_extension`, `url`, `keyboard_shortcut` oder `command` |
| `trigger_port` | Port fuer die Kommunikation mit der Extension (Standard: 59213) |
| `block_original` | `true` = Original-Mute wird blockiert |
| `trigger_on` | `press` oder `release` |
| `auto_reconnect` | Automatisch neu verbinden wenn USB-Geraet getrennt wird |

### Andere Action-Types

**URL oeffnen:**
```json
{
    "action_type": "url",
    "action": "https://app.curala"
}
```

**Tastenkombination senden:**
```json
{
    "action_type": "keyboard_shortcut",
    "action": "ctrl+shift+n"
}
```

**Shell-Befehl ausfuehren:**
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

Extension: in `chrome://extensions` einfach entfernen.

## Entwicklung

```bash
pip install -r requirements.txt
python mic_button_remap.py --run --verbose
```
