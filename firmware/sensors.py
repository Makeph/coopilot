# sensors.py -- reads the door safety inputs plus best-effort climate/resources.
# Returns one plain dict per cycle; door.py consumes the safety fields and the
# dashboard/telemetry use the rest. Missing hardware degrades to None, never a
# crash -- the door logic only needs the switches, the beam and motor current.
from machine import Pin, ADC
import config


def _active(value, active_low):
    return (value == 0) if active_low else (value == 1)


class Sensors:
    def __init__(self):
        self._limit_open = Pin(config.PIN_LIMIT_OPEN, Pin.IN, Pin.PULL_UP)
        self._limit_closed = Pin(config.PIN_LIMIT_CLOSED, Pin.IN, Pin.PULL_UP)
        self._ir = Pin(config.PIN_IR_BEAM, Pin.IN, Pin.PULL_UP)
        self._current = ADC(Pin(config.PIN_MOTOR_CURRENT))
        try:
            self._current.atten(ADC.ATTN_11DB)  # full 0..3.3V range
        except Exception:
            pass
        self._climate = _try_bme280()

    def read(self):
        return {
            "limit_open": _active(self._limit_open.value(), config.LIMIT_ACTIVE_LOW),
            "limit_closed": _active(self._limit_closed.value(), config.LIMIT_ACTIVE_LOW),
            "obstacle": _active(self._ir.value(), config.IR_ACTIVE_LOW),
            "current_a": self._read_current(),
            "temperature_c": self._climate_temp(),
            "humidity_pct": self._climate_hum(),
            # Wire your HX711 load-cell reads in here; None keeps them optional.
            "water_pct": None,
            "food_pct": None,
        }

    def _read_current(self):
        try:
            return self._current.read() / 4095 * config.MOTOR_CURRENT_FS_A
        except Exception:
            return None

    def _climate_temp(self):
        try:
            return self._climate.temperature if self._climate else None
        except Exception:
            return None

    def _climate_hum(self):
        try:
            return self._climate.humidity if self._climate else None
        except Exception:
            return None


def _try_bme280():
    # Plug a BME280 driver here (e.g. an I2C bme280 module). Returning None keeps
    # climate reporting optional -- the door never depends on it.
    return None
