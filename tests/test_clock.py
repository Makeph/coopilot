# Proves the monotonic clock survives a ticks_ms() wraparound -- so the door
# move-timeout can't be fooled after ~6 days of uptime on real hardware.
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "firmware"))

import clock


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    assert cond, name


P = clock._PERIOD

# Start just below the wrap boundary, feed small +200ms steps that cross zero.
clock._reset(P - 500)
steps = [P - 300, P - 100, 100, 300, 700]
prev = P - 500
expected_ms = 0
monotonic = True
last = clock.mono_s()
for t in steps:
    clock.tick(t)
    d = (t - prev) & (P - 1)
    if d >= P // 2:
        d -= P
    expected_ms += d
    prev = t
    if clock.mono_s() < last:
        monotonic = False
    last = clock.mono_s()

check("uptime accumulates correctly across a wrap", clock.mono_s() == expected_ms // 1000)
check("uptime never goes backward across a wrap", monotonic)

naive = 700 - (P - 500)
check("naive fixed-reference diff would be negative (the bug)", naive < 0)

# Many wraps stay exact.
clock._reset(0)
t = 0
for _ in range(1000):
    t = (t + 500) & (P - 1)
    clock.tick(t)
check("uptime exact after many wraps (500s)", clock.mono_s() == 500)

print("\nALL CLOCK TESTS PASSED")
