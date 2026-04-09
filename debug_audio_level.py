"""Debug: monitors audio input level to detect hardware mute."""
import sounddevice as sd
import numpy as np

print("=" * 60)
print("  Audio Level Monitor - Hardware Mute Detection")
print("=" * 60)
print()

# List input devices
print("Eingabegeraete:")
print("-" * 60)
devices = sd.query_devices()
for i, d in enumerate(devices):
    if d['max_input_channels'] > 0:
        print(f"  [{i}] {d['name']}  ({d['max_input_channels']} Kanaele)")

print()

# Find USB microphone
mic_idx = None
for i, d in enumerate(devices):
    if d['max_input_channels'] > 0 and 'usb' in d['name'].lower():
        mic_idx = i
        break

if mic_idx is None:
    print("USB-Mikrofon nicht gefunden. Gib die Nummer ein:")
    mic_idx = int(input("> "))

mic = devices[mic_idx]
print(f"Ueberwache: [{mic_idx}] {mic['name']}")
print()
print("Druecke den Mute-Button!")
print("Du solltest sehen wie der Level auf 0.000000 faellt.")
print("Zum Beenden: Ctrl+C")
print()

was_muted = None

def callback(indata, frames, time_info, status):
    global was_muted
    level = np.abs(indata).mean()
    max_val = np.abs(indata).max()
    all_zero = max_val == 0.0

    bar_len = int(min(level * 500, 50))
    bar = "#" * bar_len

    if all_zero:
        state = "<<< MUTE (alles null!)"
    else:
        state = ""

    is_muted = all_zero

    if was_muted is not None and is_muted != was_muted:
        if is_muted:
            print(f"\n  >>> MUTE-BUTTON GEDRUECKT! (Signal -> Stille)\n")
        else:
            print(f"\n  >>> MUTE-BUTTON GEDRUECKT! (Stille -> Signal)\n")

    was_muted = is_muted

    print(f"  Level: {level:.6f}  Max: {max_val:.6f}  [{bar:<50s}] {state}", end="\r")

try:
    with sd.InputStream(device=mic_idx, channels=1, samplerate=16000,
                        blocksize=1600, callback=callback):
        print("  Starte Aufnahme...\n")
        while True:
            sd.sleep(100)
except KeyboardInterrupt:
    print("\n\nBeende...")
except Exception as e:
    print(f"\nFehler: {e}")
    print("Versuche: pip install sounddevice")
