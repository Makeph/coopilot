# Exhaustive desktop tests for the door safety state machine. No hardware.
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "firmware"))

import config
import door


def r(limit_open=False, limit_closed=False, obstacle=False, current_a=0.0):
    return {"limit_open": limit_open, "limit_closed": limit_closed,
            "obstacle": obstacle, "current_a": current_a}


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    assert cond, name


# 1. Boots to CLOSED when the closed limit switch is engaged
d = door.DoorController()
m, st, why = d.step(r(limit_closed=True), None, 0)
check("boot at closed limit -> CLOSED, motor stop", st == door.CLOSED and m == "stop")

# 2. Open command -> OPENING, motor drives open
m, st, why = d.step(r(limit_closed=True), "open", 1)
check("command open -> OPENING", st == door.OPENING and m == "open")

# 3. A command mid-move is ignored (keeps opening, does not abort)
m, st, why = d.step(r(), "close", 2)
check("command ignored while moving", st == door.OPENING and m == "open")

# 4. Reaching the open limit -> OPEN, motor stops
m, st, why = d.step(r(limit_open=True), None, 3)
check("open limit reached -> OPEN, motor stop", st == door.OPEN and m == "stop")

# 5. Close with a clear passage -> CLOSING
m, st, why = d.step(r(limit_open=True), "close", 4)
check("command close (clear) -> CLOSING", st == door.CLOSING and m == "close")

# 6. Reaching the closed limit -> CLOSED
m, st, why = d.step(r(limit_closed=True), None, 5)
check("closed limit reached -> CLOSED", st == door.CLOSED and m == "stop")

# 7. Refuse to close while the passage is blocked (a hen is in the doorway)
d2 = door.DoorController()
d2.step(r(limit_open=True), None, 0)                      # start OPEN
m, st, why = d2.step(r(limit_open=True, obstacle=True), "close", 1)
check("close refused while blocked -> stays OPEN", st == door.OPEN and m == "stop")

# 8. Anti-pinch: an obstacle appearing mid-close reverses to opening
d3 = door.DoorController()
d3.step(r(limit_open=True), None, 0)
d3.step(r(limit_open=True), "close", 1)                   # CLOSING
m, st, why = d3.step(r(obstacle=True), None, 2)
check("obstacle mid-close -> reopen (anti-pinch)", st == door.OPENING and m == "open")

# 9. Overcurrent while moving -> FAULT, motor stops
d4 = door.DoorController()
d4.step(r(limit_closed=True), None, 0)
d4.step(r(limit_closed=True), "open", 1)                  # OPENING
m, st, why = d4.step(r(current_a=config.MOTOR_OVERCURRENT_A + 0.5), None, 2)
check("overcurrent -> FAULT + stop", st == door.FAULT and m == "stop")

# 10. Move timeout -> FAULT (limit switch never reached)
d5 = door.DoorController()
d5.step(r(limit_closed=True), None, 0)
d5.step(r(limit_closed=True), "open", 0)                  # OPENING at t=0
m, st, why = d5.step(r(), None, config.MOVE_TIMEOUT_S + 1)
check("move timeout -> FAULT", st == door.FAULT and m == "stop")

# 11. Reset from FAULT re-reads position from the limit switches
m, st, why = d5.step(r(limit_closed=True), "reset", config.MOVE_TIMEOUT_S + 2)
m, st, why = d5.step(r(limit_closed=True), None, config.MOVE_TIMEOUT_S + 3)
check("reset recovers to CLOSED", st == door.CLOSED)

# 12. Unknown position at boot (no limit engaged) -> FAULT, motor stays off
d6 = door.DoorController()
m, st, why = d6.step(r(), None, 0)
check("no limit at boot -> FAULT, motor off", st == door.FAULT and m == "stop")

# 13. Both limits engaged at once -> wiring fault
d7 = door.DoorController()
m, st, why = d7.step(r(limit_open=True, limit_closed=True), None, 0)
check("both limits engaged -> FAULT", st == door.FAULT and m == "stop")

print("\nALL DOOR TESTS PASSED")
