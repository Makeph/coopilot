# actuators.py -- H-bridge control for the pop-hole door motor.
# The door.py state machine decides direction; this only drives the pins and
# guarantees the two half-bridges are never energised at the same time.
from machine import Pin
import config


class DoorMotor:
    def __init__(self):
        self._open = Pin(config.PIN_MOTOR_OPEN, Pin.OUT)
        self._close = Pin(config.PIN_MOTOR_CLOSE, Pin.OUT)
        self.drive("stop")

    def drive(self, action):
        if action == "open":
            self._close.value(0)
            self._open.value(1)
        elif action == "close":
            self._open.value(0)
            self._close.value(1)
        else:  # stop / coast -- both low
            self._open.value(0)
            self._close.value(0)
