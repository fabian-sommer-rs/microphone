"""Debug script: monitors the microphone mute state via Windows Audio API."""
import time
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL, CoInitialize
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume, EDataFlow, ERole
from pycaw.constants import CLSID_MMDeviceEnumerator
from comtypes import CoCreateInstance
from pycaw.pycaw import IMMDeviceEnumerator

print("=" * 60)
print("  Mic Mute State Monitor")
print("=" * 60)
print()

CoInitialize()

# List all microphone/input devices
enumerator = CoCreateInstance(
    CLSID_MMDeviceEnumerator, IMMDeviceEnumerator, CLSCTX_ALL
)

# EDataFlow.eCapture = 1 (input devices)
collection = enumerator.EnumAudioEndpoints(1, 0x00000001)  # DEVICE_STATE_ACTIVE
count = collection.GetCount()

print("Aktive Mikrofone/Eingabegeraete:")
print("-" * 60)

devices_info = []
for i in range(count):
    device = collection.Item(i)
    props = device.OpenPropertyStore(0)

    # Get friendly name (PKEY_Device_FriendlyName)
    from comtypes import GUID
    from ctypes import Structure, c_int, c_wchar_p, byref, pointer
    import struct

    try:
        # PKEY_Device_FriendlyName = {a45c254e-df1c-4efd-8020-67d146a850e0}, 14
        from pycaw.pycaw import PROPERTYKEY
        pk = PROPERTYKEY()
        pk.fmtid = GUID('{a45c254e-df1c-4efd-8020-67d146a850e0}')
        pk.pid = 14
        name_prop = props.GetValue(pk)
        name = name_prop.GetValue()
    except Exception:
        name = f"Geraet {i}"

    # Get volume interface
    try:
        interface = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        mute = volume.GetMute()
        vol_level = volume.GetMasterVolumeLevel()
        vol_scalar = volume.GetMasterVolumeLevelScalar()
        print(f"  [{i}] {name}")
        print(f"      Mute: {bool(mute)}  Volume: {vol_scalar:.0%}")
        devices_info.append((name, volume))
    except Exception as e:
        print(f"  [{i}] {name} - Fehler: {e}")

if not devices_info:
    print("Keine Mikrofone gefunden!")
    exit(1)

print()
print("Ueberwache Mute-Status aller Mikrofone...")
print("Druecke den Mute-Button auf dem Mikrofon!")
print("Zum Beenden: Ctrl+C")
print()

# Poll mute state
prev_states = {}
for name, vol in devices_info:
    try:
        prev_states[name] = bool(vol.GetMute())
    except Exception:
        prev_states[name] = None

try:
    while True:
        for name, vol in devices_info:
            try:
                current_mute = bool(vol.GetMute())
                if prev_states.get(name) != current_mute:
                    status = "STUMM" if current_mute else "AKTIV"
                    print(f"  >>> AENDERUNG: {name} -> {status}")
                    prev_states[name] = current_mute
            except Exception:
                pass
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nBeende...")
