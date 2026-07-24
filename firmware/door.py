# door.py -- the autonomous door safety state machine.
#
# This is the piece the README insists must live on the microcontroller: it must
# open and close the pop-hole WITHOUT depending on the network or the phone app,
# and a closing door must stop on an obstacle, on overcurrent, on a move timeout,
# or when a limit switch is reached. All of that lives here as pure logic so it
# can be exhaustively tested on a desktop with no hardware.
#
# step() takes the latest sensor reading, an optional command, and a monotonic
# seconds clock, and returns (motor_action, state, reason). The caller drives the
# H-bridge from motor_action ("open" / "close" / "stop"); it never decides safety.
import config

CLOSED = "closed"
OPEN = "open"
OPENING = "opening"
CLOSING = "closing"
FAULT = "fault"


class DoorController:
    def __init__(self):
        self._state = None       # unknown until the limit switches are read
        self._move_started = 0
        self._fault_reason = ""

    def state(self):
        return self._state

    def fault_reason(self):
        return self._fault_reason

    def step(self, r, command, now_s):
        limit_open = r.get("limit_open", False)
        limit_closed = r.get("limit_closed", False)
        obstacle = r.get("obstacle", False)
        current = r.get("current_a")

        # Both limits engaged at once is impossible -> a switch is broken/shorted.
        if limit_open and limit_closed:
            return self._fault("both limit switches engaged (wiring fault)")

        # Determine position from the switches on first run (or after a reset).
        if self._state is None:
            if limit_closed:
                self._state = CLOSED
            elif limit_open:
                self._state = OPEN
            else:
                return self._fault("position unknown at boot")

        moving = self._state in (OPENING, CLOSING)

        # Overcurrent means the motor is stalled or jammed -> stop and latch fault.
        if moving and current is not None and current >= config.MOTOR_OVERCURRENT_A:
            return self._fault("overcurrent %.1fA" % current)

        # A move that never reaches its limit switch is a jam/broken switch.
        if moving and (now_s - self._move_started) >= config.MOVE_TIMEOUT_S:
            return self._fault("move timeout after %ds" % config.MOVE_TIMEOUT_S)

        if self._state == FAULT:
            if command == "reset":
                self._state = None          # re-read position on the next step
                self._fault_reason = ""
                return "stop", FAULT, "reset requested; re-reading position"
            return "stop", FAULT, "FAULT: " + self._fault_reason

        if self._state == OPENING:
            if limit_open:
                self._state = OPEN
                return "stop", OPEN, "fully open"
            return "open", OPENING, "opening"

        if self._state == CLOSING:
            # Anti-pinch: anything in the passage while closing -> reverse to open.
            if obstacle:
                self._state = OPENING
                self._move_started = now_s
                return "open", OPENING, "obstacle detected; reopening (anti-pinch)"
            if limit_closed:
                self._state = CLOSED
                return "stop", CLOSED, "fully closed"
            return "close", CLOSING, "closing"

        if self._state == CLOSED:
            if command == "open":
                self._state = OPENING
                self._move_started = now_s
                return "open", OPENING, "opening on command"
            return "stop", CLOSED, "closed"

        if self._state == OPEN:
            if command == "close":
                # Never start a close while the passage is blocked.
                if obstacle:
                    return "stop", OPEN, "cannot close: passage blocked"
                self._state = CLOSING
                self._move_started = now_s
                return "close", CLOSING, "closing on command"
            return "stop", OPEN, "open"

        return "stop", self._state, "idle"

    def _fault(self, why):
        self._state = FAULT
        self._fault_reason = why
        return "stop", FAULT, "FAULT: " + why
