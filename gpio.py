import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)

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

def init_gpio():
  for pin in GPIO_CONFIG:
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

def set_pin(pin, state):
  GPIO.output(pin, state)
  return True

def get_pins_state():
  states = []
  for pin in GPIO_CONFIG:
    GPIO.setup(pin, GPIO.OUT)
    state = GPIO.input(pin)
    states.append({
      "pin": pin,
      "name": GPIO_CONFIG[pin]["name"],
      "state": state
    })
  return states