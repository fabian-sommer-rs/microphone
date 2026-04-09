#!/usr/bin/env python3
"""
Mic Button Remap - Cross-platform USB microphone mute button remapper.

Intercepts the mute/mic-mute key from a USB microphone and triggers
a custom action (e.g., keyboard shortcut to start a new conversation
in a transcription program).

Works on Windows, macOS, and Linux.
"""

import json
import logging
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

logger = logging.getLogger("mic-remap")

SYSTEM = platform.system()  # "Windows", "Darwin", "Linux"
APP_NAME = "MicButtonRemap"
DEFAULT_CONFIG_PATH = Path(__file__).parent / "config.json"


def get_install_dir() -> Path:
    if SYSTEM == "Windows":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / APP_NAME
    elif SYSTEM == "Darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    else:
        return Path.home() / ".config" / APP_NAME


def load_config(config_path: Path) -> dict:
    with open(config_path) as f:
        return json.load(f)


def create_default_config(config_path: Path):
    default = {
        "device_name": "",
        "action_type": "keyboard_shortcut",
        "action": "ctrl+shift+n",
        "block_original": True,
        "trigger_on": "press",
        "auto_reconnect": True,
    }
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(default, f, indent=4)
    logger.info("Created default config at: %s", config_path)
    return default


# ---------------------------------------------------------------------------
# Action execution
# ---------------------------------------------------------------------------

def execute_action(config: dict):
    action_type = config.get("action_type", "url")
    action = config.get("action", "")

    if not action:
        logger.warning("No action configured")
        return

    if action_type == "url":
        open_url(action)
    elif action_type == "keyboard_shortcut":
        send_keyboard_shortcut(action)
    elif action_type == "command":
        logger.info("Running command: %s", action)
        try:
            subprocess.Popen(action, shell=True)
        except Exception as e:
            logger.error("Failed: %s", e)
    else:
        logger.warning("Unknown action_type: %s", action_type)


def open_url(url: str):
    """Open a URL in the default browser. Cross-platform."""
    import webbrowser
    logger.info("Opening URL: %s", url)
    webbrowser.open(url)


def send_keyboard_shortcut(shortcut: str):
    """Send a keyboard shortcut cross-platform using pynput."""
    from pynput.keyboard import Controller, Key

    keyboard = Controller()
    parts = [p.strip().lower() for p in shortcut.split("+")]

    key_map = {
        "ctrl": Key.ctrl_l, "control": Key.ctrl_l,
        "shift": Key.shift_l,
        "alt": Key.alt_l, "option": Key.alt_l,
        "cmd": Key.cmd, "command": Key.cmd, "super": Key.cmd, "win": Key.cmd,
        "tab": Key.tab, "enter": Key.enter, "return": Key.enter,
        "space": Key.space, "esc": Key.esc, "escape": Key.esc,
        "backspace": Key.backspace, "delete": Key.delete,
        "up": Key.up, "down": Key.down, "left": Key.left, "right": Key.right,
        "f1": Key.f1, "f2": Key.f2, "f3": Key.f3, "f4": Key.f4,
        "f5": Key.f5, "f6": Key.f6, "f7": Key.f7, "f8": Key.f8,
        "f9": Key.f9, "f10": Key.f10, "f11": Key.f11, "f12": Key.f12,
    }

    keys = []
    for part in parts:
        if part in key_map:
            keys.append(key_map[part])
        elif len(part) == 1:
            keys.append(part)
        else:
            logger.warning("Unknown key: %s", part)
            return

    logger.info("Sending shortcut: %s", shortcut)
    # Press all modifier keys, then the final key, then release
    for k in keys[:-1]:
        keyboard.press(k)
    keyboard.press(keys[-1])
    keyboard.release(keys[-1])
    for k in reversed(keys[:-1]):
        keyboard.release(k)


# ---------------------------------------------------------------------------
# Platform-specific mute button listeners
# ---------------------------------------------------------------------------

def listen_windows(config: dict):
    """Listen for mute key on Windows using pynput."""
    from pynput.keyboard import Key, Listener

    trigger_on = config.get("trigger_on", "press")
    block = config.get("block_original", True)
    device_filter = config.get("device_name", "").lower()

    # On Windows, USB mic mute buttons typically send Key.media_volume_mute
    # Some also send a dedicated mic mute (0x18 usage)
    target_keys = {Key.media_volume_mute}

    # Try to add platform-specific mic mute key
    try:
        from pynput.keyboard import KeyCode
        # VK_VOLUME_MUTE = 0xAD, but also check for custom media keys
        target_vks = {0xAD, 0x18}  # volume mute, mic mute
    except Exception:
        target_vks = set()

    def on_press(key):
        matched = key in target_keys
        if not matched and hasattr(key, "vk"):
            matched = key.vk in target_vks
        if matched:
            logger.info("Mute button pressed!")
            if trigger_on == "press":
                execute_action(config)
            return not block  # Return False to suppress, True to pass through

    def on_release(key):
        matched = key in target_keys
        if not matched and hasattr(key, "vk"):
            matched = key.vk in target_vks
        if matched:
            if trigger_on == "release":
                execute_action(config)
            return not block

    logger.info("Listening for mute button on Windows...")
    logger.info("Action: %s -> %s", config.get("action_type"), config.get("action"))
    logger.info("Block original mute: %s", block)

    with Listener(on_press=on_press, on_release=on_release, suppress=False) as listener:
        listener.join()


def listen_macos(config: dict):
    """Listen for mute key on macOS using Quartz event tap."""
    import Quartz
    from pynput.keyboard import Key, Listener

    trigger_on = config.get("trigger_on", "press")
    block = config.get("block_original", True)

    target_keys = {Key.media_volume_mute}

    # macOS: also try to catch the system-defined media keys via NSEvent
    # Key code 0x4A = Mute on Apple keyboards
    MUTE_KEY_CODES_MAC = {0x4A, 113}

    def on_press(key):
        matched = key in target_keys
        if not matched and hasattr(key, "vk"):
            matched = key.vk in MUTE_KEY_CODES_MAC
        if matched:
            logger.info("Mute button pressed!")
            if trigger_on == "press":
                execute_action(config)
            return not block

    def on_release(key):
        matched = key in target_keys
        if not matched and hasattr(key, "vk"):
            matched = key.vk in MUTE_KEY_CODES_MAC
        if matched:
            if trigger_on == "release":
                execute_action(config)
            return not block

    logger.info("Listening for mute button on macOS...")
    logger.info("Action: %s -> %s", config.get("action_type"), config.get("action"))
    logger.info("NOTE: macOS requires Accessibility permissions for this app.")
    logger.info("Go to: System Settings > Privacy & Security > Accessibility")

    with Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


def listen_linux(config: dict):
    """Listen for mute key on Linux using evdev (device-specific)."""
    import evdev
    from evdev import InputDevice, ecodes

    device_filter = config.get("device_name", "").lower() or None
    trigger_on = config.get("trigger_on", "press")
    block = config.get("block_original", True)
    target_keystate = 1 if trigger_on == "press" else 0

    MUTE_KEYS = {113, 248, 190}  # KEY_MUTE, KEY_MICMUTE, KEY_F20

    def find_device():
        for path in evdev.list_devices():
            dev = InputDevice(path)
            caps = dev.capabilities()
            if ecodes.EV_KEY not in caps:
                continue
            name = dev.name.lower()
            if device_filter and device_filter in name:
                return dev
            if not device_filter:
                if any(kw in name for kw in ["microphone", "headset", "usb mic", "usb audio"]):
                    return dev
        return None

    logger.info("Listening for mute button on Linux...")

    while True:
        device = find_device()
        if not device:
            logger.info("Waiting for USB microphone...")
            time.sleep(2)
            continue

        logger.info("Found: %s (%s)", device.name, device.path)

        if block:
            device.grab()

        try:
            for event in device.read_loop():
                if event.type == ecodes.EV_KEY and event.code in MUTE_KEYS:
                    if event.value == target_keystate:
                        logger.info("Mute button triggered!")
                        execute_action(config)
        except OSError:
            logger.warning("Device disconnected")
        finally:
            if block:
                try:
                    device.ungrab()
                except OSError:
                    pass

        if not config.get("auto_reconnect", True):
            break
        time.sleep(3)


# ---------------------------------------------------------------------------
# Autostart installation
# ---------------------------------------------------------------------------

def install_autostart():
    """Install the app to run on system startup."""
    install_dir = get_install_dir()
    install_dir.mkdir(parents=True, exist_ok=True)

    script_src = Path(__file__).resolve()
    config_src = script_src.parent / "config.json"

    if SYSTEM == "Windows":
        _install_windows(install_dir, script_src, config_src)
    elif SYSTEM == "Darwin":
        _install_macos(install_dir, script_src, config_src)
    else:
        _install_linux(install_dir, script_src, config_src)


def _install_windows(install_dir: Path, script_src: Path, config_src: Path):
    import shutil

    # Copy files
    shutil.copy2(script_src, install_dir / "mic_button_remap.py")
    if config_src.exists():
        shutil.copy2(config_src, install_dir / "config.json")
    else:
        create_default_config(install_dir / "config.json")

    # Create a .bat launcher
    bat_path = install_dir / "mic_button_remap.bat"
    bat_path.write_text(
        f'@echo off\r\npythonw "{install_dir / "mic_button_remap.py"}" --run\r\n'
    )

    # Add to Windows startup via registry
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE,
        )
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, str(bat_path))
        winreg.CloseKey(key)
        print(f"[OK] Installed to autostart (Registry)")
    except Exception as e:
        # Fallback: copy to Startup folder
        startup = Path(os.environ.get("APPDATA", "")) / r"Microsoft\Windows\Start Menu\Programs\Startup"
        if startup.exists():
            shutil.copy2(bat_path, startup / "mic_button_remap.bat")
            print(f"[OK] Installed to Startup folder")
        else:
            print(f"[ERROR] Could not add to autostart: {e}")

    print(f"[OK] Files installed to: {install_dir}")
    print(f"[OK] Config file: {install_dir / 'config.json'}")
    print(f"[OK] MicButtonRemap will start automatically on next login.")


def _install_macos(install_dir: Path, script_src: Path, config_src: Path):
    import shutil

    shutil.copy2(script_src, install_dir / "mic_button_remap.py")
    if config_src.exists():
        shutil.copy2(config_src, install_dir / "config.json")
    else:
        create_default_config(install_dir / "config.json")

    # Create LaunchAgent plist
    plist_dir = Path.home() / "Library" / "LaunchAgents"
    plist_dir.mkdir(parents=True, exist_ok=True)
    plist_path = plist_dir / "com.micbuttonremap.agent.plist"

    python_path = sys.executable
    script_path = install_dir / "mic_button_remap.py"

    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.micbuttonremap.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_path}</string>
        <string>{script_path}</string>
        <string>--run</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{install_dir / "stdout.log"}</string>
    <key>StandardErrorPath</key>
    <string>{install_dir / "stderr.log"}</string>
</dict>
</plist>"""

    plist_path.write_text(plist_content)

    # Load the agent
    subprocess.run(["launchctl", "load", str(plist_path)], check=False)

    print(f"[OK] Files installed to: {install_dir}")
    print(f"[OK] Config file: {install_dir / 'config.json'}")
    print(f"[OK] LaunchAgent installed: {plist_path}")
    print(f"[OK] MicButtonRemap will start automatically on next login.")
    print()
    print("[IMPORTANT] macOS requires Accessibility permissions:")
    print("  System Settings > Privacy & Security > Accessibility")
    print(f"  Add: {python_path}")


def _install_linux(install_dir: Path, script_src: Path, config_src: Path):
    import shutil

    shutil.copy2(script_src, install_dir / "mic_button_remap.py")
    if config_src.exists():
        shutil.copy2(config_src, install_dir / "config.json")
    else:
        create_default_config(install_dir / "config.json")

    # Create systemd user service
    systemd_dir = Path.home() / ".config" / "systemd" / "user"
    systemd_dir.mkdir(parents=True, exist_ok=True)
    service_path = systemd_dir / "mic-button-remap.service"

    service_content = f"""[Unit]
Description=Mic Button Remap
After=default.target

[Service]
ExecStart={sys.executable} {install_dir / "mic_button_remap.py"} --run
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
"""

    service_path.write_text(service_content)
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
    subprocess.run(["systemctl", "--user", "enable", "mic-button-remap"], check=False)
    subprocess.run(["systemctl", "--user", "start", "mic-button-remap"], check=False)

    print(f"[OK] Files installed to: {install_dir}")
    print(f"[OK] Config file: {install_dir / 'config.json'}")
    print(f"[OK] Systemd service installed and started")


def uninstall_autostart():
    """Remove autostart configuration."""
    install_dir = get_install_dir()

    if SYSTEM == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE,
            )
            winreg.DeleteValue(key, APP_NAME)
            winreg.CloseKey(key)
        except Exception:
            pass
        startup = Path(os.environ.get("APPDATA", "")) / r"Microsoft\Windows\Start Menu\Programs\Startup"
        bat = startup / "mic_button_remap.bat"
        if bat.exists():
            bat.unlink()

    elif SYSTEM == "Darwin":
        plist = Path.home() / "Library" / "LaunchAgents" / "com.micbuttonremap.agent.plist"
        if plist.exists():
            subprocess.run(["launchctl", "unload", str(plist)], check=False)
            plist.unlink()

    else:
        subprocess.run(["systemctl", "--user", "stop", "mic-button-remap"], check=False)
        subprocess.run(["systemctl", "--user", "disable", "mic-button-remap"], check=False)
        service = Path.home() / ".config" / "systemd" / "user" / "mic-button-remap.service"
        if service.exists():
            service.unlink()

    import shutil
    if install_dir.exists():
        shutil.rmtree(install_dir)

    print(f"[OK] {APP_NAME} uninstalled.")


# ---------------------------------------------------------------------------
# System tray icon (optional, for Windows/Mac)
# ---------------------------------------------------------------------------

def run_with_tray(config: dict):
    """Run the listener with a system tray icon for easy exit."""
    try:
        import pystray
        from PIL import Image, ImageDraw
    except ImportError:
        # No tray icon support, run headless
        run_headless(config)
        return

    import threading

    def create_icon_image():
        img = Image.new("RGB", (64, 64), color=(40, 40, 40))
        draw = ImageDraw.Draw(img)
        # Simple microphone icon
        draw.ellipse([22, 8, 42, 32], fill=(0, 180, 0))
        draw.rectangle([28, 32, 36, 44], fill=(0, 180, 0))
        draw.arc([18, 24, 46, 50], 0, 180, fill=(0, 180, 0), width=3)
        draw.line([32, 50, 32, 58], fill=(0, 180, 0), width=3)
        draw.line([22, 58, 42, 58], fill=(0, 180, 0), width=3)
        return img

    def on_quit(icon, item):
        icon.stop()
        os._exit(0)

    def on_open_config(icon, item):
        config_path = get_install_dir() / "config.json"
        if not config_path.exists():
            config_path = DEFAULT_CONFIG_PATH
        if SYSTEM == "Windows":
            os.startfile(str(config_path))
        elif SYSTEM == "Darwin":
            subprocess.Popen(["open", str(config_path)])
        else:
            subprocess.Popen(["xdg-open", str(config_path)])

    menu = pystray.Menu(
        pystray.MenuItem("Mic Button Remap", None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Open Config", on_open_config),
        pystray.MenuItem("Quit", on_quit),
    )

    icon = pystray.Icon(APP_NAME, create_icon_image(), "Mic Button Remap", menu)

    # Start listener in background thread
    listener_thread = threading.Thread(target=run_headless, args=(config,), daemon=True)
    listener_thread.start()

    icon.run()


def run_headless(config: dict):
    """Run the listener without tray icon."""
    if SYSTEM == "Windows":
        listen_windows(config)
    elif SYSTEM == "Darwin":
        listen_macos(config)
    else:
        listen_linux(config)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Remap USB microphone mute button")
    parser.add_argument("--install", action="store_true", help="Install and add to autostart")
    parser.add_argument("--uninstall", action="store_true", help="Remove from autostart")
    parser.add_argument("--run", action="store_true", help="Run the listener")
    parser.add_argument("--config", "-c", type=Path, default=None, help="Config file path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    parser.add_argument("--no-tray", action="store_true", help="Run without system tray icon")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    if args.install:
        install_autostart()
        return

    if args.uninstall:
        uninstall_autostart()
        return

    # Determine config path
    config_path = args.config
    if not config_path:
        installed = get_install_dir() / "config.json"
        if installed.exists():
            config_path = installed
        elif DEFAULT_CONFIG_PATH.exists():
            config_path = DEFAULT_CONFIG_PATH
        else:
            config_path = DEFAULT_CONFIG_PATH
            create_default_config(config_path)

    config = load_config(config_path)
    logger.info("Config loaded from: %s", config_path)

    if args.no_tray:
        run_headless(config)
    else:
        run_with_tray(config)


if __name__ == "__main__":
    main()
