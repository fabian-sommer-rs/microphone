#!/usr/bin/env python3
"""
Remap USB Microphone Mute Button

Listens for the mute button press on a USB microphone and triggers
a configurable action (e.g., start a new conversation in a transcription program).

Requires: python-evdev (pip install evdev)
Must run with permissions to read /dev/input/* devices (root or udev rule).
"""

import argparse
import json
import logging
import subprocess
import sys
import time
from pathlib import Path

import evdev
from evdev import InputDevice, categorize, ecodes

logger = logging.getLogger("mic-button-remap")

DEFAULT_CONFIG_PATH = Path(__file__).parent / "config.json"

# Common key codes for USB microphone mute buttons
MUTE_KEY_CODES = {
    ecodes.KEY_MUTE,       # 113 - most common
    ecodes.KEY_MICMUTE,    # 248 - dedicated mic mute
    ecodes.KEY_F20,        # 190 - some headsets use this
}


def load_config(config_path: Path) -> dict:
    """Load configuration from JSON file."""
    with open(config_path) as f:
        return json.load(f)


def find_mic_device(device_name_filter: str | None = None) -> InputDevice | None:
    """Find the USB microphone input device.

    Args:
        device_name_filter: Substring to match against device names.
                           If None, searches for common USB mic patterns.
    """
    devices = [InputDevice(path) for path in evdev.list_devices()]

    for device in devices:
        caps = device.capabilities(verbose=True)
        has_keys = ("EV_KEY", ecodes.EV_KEY) in caps

        if not has_keys:
            continue

        name_lower = device.name.lower()

        if device_name_filter:
            if device_name_filter.lower() in name_lower:
                logger.info("Found matching device: %s (%s)", device.name, device.path)
                return device
        else:
            # Look for common USB microphone identifiers
            mic_keywords = ["microphone", "headset", "usb mic", "usb audio"]
            if any(kw in name_lower for kw in mic_keywords):
                logger.info("Found USB mic device: %s (%s)", device.name, device.path)
                return device

    return None


def list_devices():
    """List all input devices with their capabilities (for debugging)."""
    devices = [InputDevice(path) for path in evdev.list_devices()]

    if not devices:
        print("No input devices found. Are you running with sufficient permissions?")
        return

    print(f"{'Path':<20} {'Name':<45} {'Has Keys'}")
    print("-" * 75)

    for device in devices:
        caps = device.capabilities(verbose=True)
        has_keys = ("EV_KEY", ecodes.EV_KEY) in caps
        print(f"{device.path:<20} {device.name:<45} {has_keys}")

        if has_keys:
            key_caps = device.capabilities().get(ecodes.EV_KEY, [])
            mute_keys_present = MUTE_KEY_CODES.intersection(set(key_caps))
            if mute_keys_present:
                names = [ecodes.KEY[k] for k in mute_keys_present]
                print(f"  -> Mute keys found: {', '.join(names)}")


def monitor_device(device: InputDevice):
    """Monitor all events from a device (for debugging / finding key codes)."""
    print(f"Monitoring events from: {device.name} ({device.path})")
    print("Press the mute button to see its event. Press Ctrl+C to stop.\n")

    try:
        for event in device.read_loop():
            if event.type == ecodes.EV_KEY:
                key_event = categorize(event)
                state = "pressed" if key_event.keystate == 1 else (
                    "released" if key_event.keystate == 0 else "held"
                )
                print(f"Key: {key_event.keycode}  Code: {event.code}  State: {state}")
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")


def execute_action(config: dict):
    """Execute the configured action when the button is pressed."""
    action_type = config.get("action_type", "command")
    action = config.get("action")

    if not action:
        logger.warning("No action configured")
        return

    if action_type == "command":
        logger.info("Executing command: %s", action)
        try:
            subprocess.Popen(action, shell=True)
        except Exception as e:
            logger.error("Failed to execute command: %s", e)

    elif action_type == "xdotool":
        # Simulate keyboard shortcut using xdotool
        logger.info("Sending keyboard shortcut: %s", action)
        try:
            subprocess.Popen(["xdotool", "key", action])
        except FileNotFoundError:
            logger.error("xdotool not installed. Install with: sudo apt install xdotool")
        except Exception as e:
            logger.error("Failed to send shortcut: %s", e)

    elif action_type == "dbus":
        logger.info("Sending DBus signal: %s", action)
        try:
            subprocess.Popen(["dbus-send"] + action.split())
        except Exception as e:
            logger.error("Failed to send DBus signal: %s", e)

    else:
        logger.warning("Unknown action type: %s", action_type)


def grab_and_listen(device: InputDevice, config: dict):
    """Grab the device (block original mute behavior) and listen for button presses."""
    key_codes = set(config.get("key_codes", []))
    if not key_codes:
        key_codes = MUTE_KEY_CODES

    trigger_on = config.get("trigger_on", "press")  # "press" or "release"
    target_keystate = 1 if trigger_on == "press" else 0

    grab = config.get("grab_device", True)

    device_name = device.name
    logger.info("Listening on: %s (%s)", device_name, device.path)
    logger.info("Watching for key codes: %s", key_codes)
    logger.info("Trigger on: %s", trigger_on)
    logger.info("Grab device (block original event): %s", grab)

    if grab:
        device.grab()
        logger.info("Device grabbed - original mute event is now blocked")

    try:
        for event in device.read_loop():
            if event.type == ecodes.EV_KEY and event.code in key_codes:
                if event.value == target_keystate:
                    logger.info("Button %s! Triggering action...", trigger_on)
                    execute_action(config)
    except KeyboardInterrupt:
        logger.info("Stopped by user")
    except OSError as e:
        logger.error("Device disconnected or error: %s", e)
    finally:
        if grab:
            try:
                device.ungrab()
            except OSError:
                pass


def wait_for_device(device_name_filter: str | None, poll_interval: float = 2.0) -> InputDevice:
    """Wait until the USB microphone device appears."""
    logger.info("Waiting for USB microphone device...")
    while True:
        device = find_mic_device(device_name_filter)
        if device:
            return device
        time.sleep(poll_interval)


def main():
    parser = argparse.ArgumentParser(
        description="Remap USB microphone mute button to a custom action"
    )
    parser.add_argument(
        "--config", "-c",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to config file (default: config.json in script directory)",
    )
    parser.add_argument(
        "--list-devices", "-l",
        action="store_true",
        help="List all input devices and exit",
    )
    parser.add_argument(
        "--monitor", "-m",
        type=str,
        metavar="DEVICE_FILTER",
        nargs="?",
        const="",
        help="Monitor events from a device (to find key codes). "
             "Optionally filter by device name substring.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # List devices mode
    if args.list_devices:
        list_devices()
        return

    # Monitor mode
    if args.monitor is not None:
        device_filter = args.monitor if args.monitor else None
        device = find_mic_device(device_filter)
        if not device:
            print("No matching device found. Use --list-devices to see all devices.")
            sys.exit(1)
        monitor_device(device)
        return

    # Normal operation: load config and start listening
    if not args.config.exists():
        logger.error("Config file not found: %s", args.config)
        logger.error("Copy config.example.json to config.json and adjust settings.")
        sys.exit(1)

    config = load_config(args.config)
    device_name = config.get("device_name")
    auto_reconnect = config.get("auto_reconnect", True)

    while True:
        device = wait_for_device(device_name)
        grab_and_listen(device, config)

        if not auto_reconnect:
            break

        logger.info("Device lost. Will attempt to reconnect in 3 seconds...")
        time.sleep(3)


if __name__ == "__main__":
    main()
