"""Debug script: monitors raw USB HID reports to find the mic button signal."""
import time
import pywinusb.hid as hid

print("=" * 60)
print("  USB HID Debugger - Rohdaten vom Mikrofon")
print("=" * 60)
print()

# List all HID devices
all_devices = hid.HidDeviceFilter().get_devices()

print("Alle HID-Geraete:")
print("-" * 60)
for i, device in enumerate(all_devices):
    name = device.product_name or "(unbekannt)"
    vid = device.vendor_id
    pid = device.product_id
    print(f"  [{i:2d}] {name}  (VID=0x{vid:04X}  PID=0x{pid:04X})")
print()

# Find microphone devices
mic_devices = []
for device in all_devices:
    name = (device.product_name or "").lower()
    if any(kw in name for kw in ["microphone", "mikrofon", "mic", "headset", "fyvadio", "usb audio", "conference"]):
        mic_devices.append(device)

if not mic_devices:
    print("Kein Mikrofon-HID-Geraet gefunden.")
    print()
    print("Gib die Nummer eines Geraets ein, das du ueberwachen willst:")
    try:
        idx = int(input("> "))
        mic_devices = [all_devices[idx]]
    except (ValueError, IndexError):
        print("Ungueltig. Beende.")
        exit(1)

def make_handler(device_name):
    def handler(data):
        hex_data = " ".join(f"{b:02X}" for b in data)
        print(f"[HID] {device_name}: {hex_data}")
    return handler

print(f"Ueberwache {len(mic_devices)} Geraet(e):")
for device in mic_devices:
    name = device.product_name or "(unbekannt)"
    print(f"  -> {name} (VID=0x{device.vendor_id:04X} PID=0x{device.product_id:04X})")

print()
print("Druecke jetzt den Mute-Button auf dem Mikrofon!")
print("Zum Beenden: Ctrl+C")
print()

for device in mic_devices:
    try:
        device.open()
        device.set_raw_data_handler(make_handler(device.product_name or "?"))
    except Exception as e:
        print(f"  FEHLER beim Oeffnen: {e}")

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nBeende...")
finally:
    for device in mic_devices:
        try:
            device.close()
        except Exception:
            pass
