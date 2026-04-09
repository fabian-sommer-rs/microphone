"""Debug script: shows ALL key events to find the mic button's key code."""
from pynput.keyboard import Key, Listener, KeyCode

print("=" * 50)
print("  Mic Button Debugger")
print("=" * 50)
print()
print("Druecke den Mute-Button auf dem Mikrofon!")
print("Alle Tasten werden hier angezeigt.")
print("Zum Beenden: Ctrl+C")
print()

def on_press(key):
    vk = getattr(key, "vk", None)
    name = getattr(key, "name", None)
    char = getattr(key, "char", None)

    print(f"[PRESS]   key={key!r:30s}  vk={vk:#06x if vk else 'None':>8s}  name={name}  char={char}")

def on_release(key):
    vk = getattr(key, "vk", None)
    name = getattr(key, "name", None)

    print(f"[RELEASE] key={key!r:30s}  vk={vk:#06x if vk else 'None':>8s}  name={name}")

with Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
