# clock.py -- monotonic uptime in seconds that never wraps.
#
# time.ticks_ms() on the ESP32 wraps roughly every 12 days, and time.ticks_diff()
# is only valid over half that span. The door timeout and dwell logic depend on
# elapsed time, so a naive uptime that breaks after ~6 days would eventually let
# a stuck motor run past its safety timeout. We accumulate the small deltas
# between successive ticks instead: as long as tick() is called far more often
# than the wrap period (the control loop runs several times a second) uptime is
# exact and unbounded.
import time

_PERIOD = 1 << 30  # MicroPython ESP32 ticks_ms period (ms)

if hasattr(time, "ticks_ms"):          # MicroPython, on the device
    _ticks = time.ticks_ms
    _diff = time.ticks_diff
else:                                  # CPython, for desktop tests
    _t0 = time.time()

    def _ticks():
        return int((time.time() - _t0) * 1000) & (_PERIOD - 1)

    def _diff(a, b):
        d = (a - b) & (_PERIOD - 1)
        return d - _PERIOD if d >= _PERIOD // 2 else d

_last = _ticks()
_acc_ms = 0


def tick(now_ms=None):
    """Advance the clock and return whole seconds of uptime. Call every loop.

    `now_ms` is a test hook to feed synthetic tick values; production passes None.
    """
    global _last, _acc_ms
    now = _ticks() if now_ms is None else now_ms
    _acc_ms += _diff(now, _last)
    _last = now
    return _acc_ms // 1000


def mono_s():
    """Whole seconds of uptime, without advancing the clock."""
    return _acc_ms // 1000


def _reset(now_ms=0):
    """Test hook: reset the accumulator to a known tick value."""
    global _last, _acc_ms
    _last = now_ms
    _acc_ms = 0
