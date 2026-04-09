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
    vk_str = f"0x{vk:04X}" if vk is not None else "None"

    print(f"[PRESS]   key={key!r}  vk={vk_str}  name={name}  char={char}")

def on_release(key):
    vk = getattr(key, "vk", None)
    name = getattr(key, "name", None)
    vk_str = f"0x{vk:04X}" if vk is not None else "None"

    print(f"[RELEASE] key={key!r}  vk={vk_str}  name={name}")

with Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
