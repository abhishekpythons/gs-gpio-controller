import RPi.GPIO as GPIO
import time
from threading import Lock

# ----------------------------
# GPIO MODE
# ----------------------------
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# ----------------------------
# GPIO CONFIG
# ----------------------------
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

# ----------------------------
# INTERNAL STATE
# ----------------------------
_gpio_lock = Lock()
_gpio_state = {}        # pin -> 0/1
_last_toggle = {}       # pin -> timestamp
MIN_TOGGLE_INTERVAL = 0.5  # seconds (relay-safe)

# ----------------------------
# INITIALISATION
# ----------------------------
def init_gpio():
    """
    Initialise all GPIO pins to a known safe LOW state.
    Must be called ONCE at server startup.
    """
    with _gpio_lock:
        for pin in GPIO_CONFIG:
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
            _gpio_state[pin] = GPIO.LOW
            _last_toggle[pin] = 0.0

# ----------------------------
# SET PIN (SAFE)
# ----------------------------
def set_pin(pin, state):
    """
    Safely set a GPIO pin HIGH/LOW with debounce and locking.
    """
    if pin not in GPIO_CONFIG:
        return False, "Invalid pin"

    state = GPIO.HIGH if state else GPIO.LOW
    now = time.time()

    with _gpio_lock:
        # debounce / rate-limit
        if now - _last_toggle[pin] < MIN_TOGGLE_INTERVAL:
            return False, "Toggle rate limit"

        GPIO.output(pin, state)
        _gpio_state[pin] = state
        _last_toggle[pin] = now

    return True, "OK"

# ----------------------------
# GET ALL PIN STATES (CACHED)
# ----------------------------
def get_pins_state():
    """
    Return cached GPIO states (no hardware read).
    """
    with _gpio_lock:
        return [
            {
                "pin": pin,
                "name": GPIO_CONFIG[pin]["name"],
                "state": _gpio_state.get(pin, GPIO.LOW),
            }
            for pin in GPIO_CONFIG
        ]

# ----------------------------
# FORCE ALL LOW (EMERGENCY / SHUTDOWN)
# ----------------------------
def all_off():
    """
    Force all GPIO pins LOW.
    """
    with _gpio_lock:
        for pin in GPIO_CONFIG:
            GPIO.output(pin, GPIO.LOW)
            _gpio_state[pin] = GPIO.LOW

# ----------------------------
# CLEANUP
# ----------------------------
def cleanup():
    """
    Cleanup GPIO safely.
    """
    all_off()
    GPIO.cleanup()
