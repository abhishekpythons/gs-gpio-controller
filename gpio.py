from gpiozero import LED

# Define GPIO pins you want to control
GPIO_CONFIG = {
    35: {"name": "NuC PC"},
    37: {"name": "SDR RF Frontend"},
    33: {"name": "G5500 Rotator"},
    31: {"name": "VHF SSPA"},
    36: {"name": "UHF SSPA"},
    38: {"name": "Cooling Fan"},
    40: {"name": "Light"},
    29: {"name": "Spare"},
}

gpio_devices = {
    pin: LED(pin) for pin in GPIO_CONFIG
}

def get_pins_state():
    return [
        {
            "pin": pin,
            "name": GPIO_CONFIG[pin]["name"],
            "state": 1 if dev.is_lit else 0
        }
        for pin, dev in gpio_devices.items()
    ]

def set_pin(pin, state):
    dev = gpio_devices.get(pin)
    if not dev:
        return False
    dev.on() if state else dev.off()
    return True
