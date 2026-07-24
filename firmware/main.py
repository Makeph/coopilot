# main.py -- the control loop. Reads sensors, runs the door safety FSM, drives
# the motor, applies the daily open/close schedule, and publishes telemetry.
# Every cycle is wrapped: one bad read is logged and skipped, never fatal. The
# door logic is fully autonomous -- WiFi/MQTT only add the remote view.
import time
import config
import boot
import clock
import scheduler
import sensors
import actuators
import door

if boot.wifi_ok():
    scheduler.sync_clock()

_tele = None
try:
    import telemetry
    _tele = telemetry.Telemetry()
except Exception as e:
    print("main: telemetry disabled:", e)

_sense = sensors.Sensors()
_motor = actuators.DoorMotor()
_door = door.DoorController()

STATE = {
    "uptime_s": 0,
    "door": None,
    "door_reason": "",
    "motor": "stop",
    "temperature_c": None,
    "humidity_pct": None,
    "water_pct": None,
    "food_pct": None,
    "alerts": [],
    "device_online": False,
}


def _alerts(r):
    a = []
    w, f, t = r.get("water_pct"), r.get("food_pct"), r.get("temperature_c")
    if w is not None and w < config.WATER_LOW_PCT:
        a.append("water_low")
    if f is not None and f < config.FOOD_LOW_PCT:
        a.append("food_low")
    if t is not None and t < config.TEMP_LOW_C:
        a.append("temp_low")
    if t is not None and t > config.TEMP_HIGH_C:
        a.append("temp_high")
    return a


def _cycle():
    now_s = clock.tick()
    r = _sense.read()
    command = scheduler.scheduled_command(scheduler.local_hour())

    motor, dstate, reason = _door.step(r, command, now_s)
    _motor.drive(motor)

    STATE["uptime_s"] = now_s
    STATE["door"] = dstate
    STATE["door_reason"] = reason
    STATE["motor"] = motor
    STATE["temperature_c"] = r["temperature_c"]
    STATE["humidity_pct"] = r["humidity_pct"]
    STATE["water_pct"] = r["water_pct"]
    STATE["food_pct"] = r["food_pct"]
    STATE["alerts"] = _alerts(r)
    STATE["device_online"] = boot.wifi_ok()

    print("t=+%ds door=%s motor=%s%s | temp=%s hum=%s" % (
        now_s, dstate, motor,
        (" ALERTS:" + ",".join(STATE["alerts"])) if STATE["alerts"] else "",
        "--" if r["temperature_c"] is None else ("%.1f" % r["temperature_c"]),
        "--" if r["humidity_pct"] is None else ("%d" % r["humidity_pct"])))

    if _tele is not None:
        _tele.publish(STATE)


def run():
    next_cycle = time.ticks_ms()
    while True:
        try:
            if time.ticks_diff(time.ticks_ms(), next_cycle) >= 0:
                _cycle()
                next_cycle = time.ticks_add(time.ticks_ms(), config.SENSE_INTERVAL_S * 1000)
            time.sleep_ms(100)
        except Exception as e:
            print("main: cycle error (continuing):", e)
            _motor.drive("stop")  # fail safe: cut the motor on any error
            time.sleep_ms(500)


run()
