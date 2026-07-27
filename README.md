# 🐔 Coopilot — connected chicken-coop controller

[![CI](https://github.com/Makeph/coopilot/actions/workflows/ci.yml/badge.svg)](https://github.com/Makeph/coopilot/actions/workflows/ci.yml)

An **offline-first** controller for a small connected coop: an autonomous pop-hole
door with real safety interlocks, climate and resource monitoring, and a local
web dashboard. The door logic lives **entirely on the ESP32** and keeps working
with no network, no cloud and no phone — WiFi only adds NTP time and the remote
view.

The safety-critical part — *"a closing door must stop on an obstacle, on
overcurrent, on a move timeout, or when a limit switch is reached"* — is a small
state machine ([`firmware/door.py`](firmware/door.py)) that is exhaustively
unit-tested on a desktop with no hardware.

---

## What's in the box

| Layer | Path | What it does |
|---|---|---|
| **Firmware** | [`firmware/`](firmware/) | MicroPython for the ESP32: door safety FSM, sensors, motor driver, daily schedule, best-effort MQTT telemetry, and a wrap-safe uptime clock. |
| **Dashboard** | [`dashboard/`](dashboard/) | A dependency-free web UI. Ships with a browser **simulator** (`sim.js`) so it runs as a live demo; swap it for a real MQTT-over-WebSocket feed for production. |
| **Tests** | [`tests/`](tests/) | Host tests for the door FSM and the clock — `python run_tests.py`, no hardware. |

---

## Try the dashboard (no hardware)

```bash
cd dashboard
python -m http.server 8091
# open http://localhost:8091
```

The page runs on a built-in simulation: the climate drifts, the water and feed
deplete, and the door works. Press **Fermer la porte** to close it; flip
**Passage libre → 🐔 Passage bloqué** and try again to see the door **refuse to
close on a blocked passage**, or block it mid-travel to watch the **anti-pinch
reopen** — the exact rules the firmware enforces.

---

## The door safety machine

`firmware/door.py` is deliberately hardware-free logic. Each cycle it takes the
limit switches, the anti-pinch beam and the motor current, plus an optional
command, and returns `(motor_action, state, reason)`:

- **Refuses to close** while the passage beam is broken.
- **Anti-pinch:** an obstacle appearing mid-close **reverses to open**.
- **Overcurrent** (stalled/jammed motor) → stop and latch a **FAULT**.
- **Move timeout** (a limit switch never reached) → **FAULT**.
- **Unknown position** at boot, or both limit switches engaged (wiring fault) →
  **FAULT**, motor off, until an explicit `reset`.

Because the caller only drives the H-bridge from `motor_action`, the safety
decision can never be bypassed by the network or the app.

---

## Bill of materials

| Part | Purpose | ~Price (EUR) |
|------|---------|--------------|
| ESP32 devkit (WROOM-32) | brain + WiFi | 5 |
| BME280 | air temperature + humidity | 3 |
| 2× HX711 + load cells | water & feed levels | 6 |
| 2× limit switches | door fully open / fully closed | 2 |
| IR beam sensor | passage presence / anti-pinch | 3 |
| 12 V gearmotor + H-bridge | drives the pop-hole door | 8 |
| 12 V supply, 5 V buck, fuse, e-stop, IP65 box | power + protection | 12 |

Wire the mains/12 V side with proper fusing and an enclosure, and **always keep a
manual mechanical door override**. See the safety notes below.

---

## Flashing the firmware

```bash
pip install esptool mpremote
esptool.py --chip esp32 --port COM5 erase_flash
esptool.py --chip esp32 --port COM5 --baud 460800 write_flash -z 0x1000 ESP32_GENERIC-*.bin
mpremote connect COM5 fs cp firmware/*.py :
mpremote connect COM5 reset
```

Edit pins, safety thresholds and the daily open/close hours in
[`firmware/config.py`](firmware/config.py) — nothing else needs touching.

---

## Data contract (MQTT)

With a broker configured in `config.py`, the firmware publishes:

```text
coop/climate      {"temperature_c": 18.6, "humidity_pct": 61}
coop/resources    {"water_pct": 32, "food_pct": 68}
coop/door/state   "open" | "closed" | "opening" | "closing" | "fault"
coop/alerts       ["water_low", ...]
```

The dashboard consumes the same shape; the simulator emits it too, so wiring a
real feed later is a drop-in change.

---

## Reliability & testing

```bash
python run_tests.py
```

No hardware, no dependencies. It covers the full door FSM (open/close, refuse,
anti-pinch, overcurrent, timeout, wiring faults, reset) and the **monotonic
uptime clock**, including a simulated `ticks_ms()` wraparound: on the ESP32
`time.ticks_ms()` wraps ~every 12 days and `ticks_diff()` is only valid over half
of that, so a naive uptime would break after ~6 days and could let a stuck motor
run past its safety timeout. [`firmware/clock.py`](firmware/clock.py) accumulates
deltas instead. CI runs the suite and `ruff` on every push.

---

## Safety disclaimer

This is hobbyist automation driving a **motor near live animals** and, on the
load side, likely **mains voltage**. A pinch or a jam can hurt a bird. Use rated
components, fuse the power side, keep an independent manual override, and test the
low-voltage logic thoroughly before trusting the door unattended. The firmware
interlocks reduce risk; they do not remove your responsibility for a safe build.

---

MIT-licensed. Runs on your bench and in your garden, with nothing to sign into.

---

<!-- hiddengrid-stack -->

## Part of the HiddenGrid edge stack

Eight small repos, one chain: **control → transport → hub → supervision**. Each one
stands alone and runs offline; together they are a working local-first stack with no
cloud account anywhere in it.

| | Repo | What it does |
|---|---|---|
| Control  | [greenhouse](https://github.com/Makeph/greenhouse) | ESP32/MicroPython greenhouse controller — light, aeration, heat and pulse irrigation. Safety lives in firmware. |
| Control → | **coopilot** | ESP32/MicroPython coop controller — pop-hole door with anti-pinch, overcurrent and timeout interlocks. |
| Transport  | [gorilla-tsc](https://github.com/Makeph/gorilla-tsc) | Lossless Gorilla time-series compression — the codec the edge→hub link stores with. |
| Hub  | [plexus](https://github.com/Makeph/plexus) | MQTT ingest → compressed store → drift & stuck-sensor detection → one dashboard. Stdlib only. |
| Product  | [serra](https://github.com/Makeph/serra) | Multi-site supervision for greenhouses & aquaponics, built on plexus. |
| Industry  | [industrial-retrofit](https://github.com/Makeph/industrial-retrofit) | Real Modbus-TCP off a legacy PLC → clean telemetry, anomalies, live OEE. |
| Industry  | [line-twin](https://github.com/Makeph/line-twin) | Measured cycle times → the bottleneck → the ROI of fixing it. |
| Industry  | [kiln-retrofit](https://github.com/Makeph/kiln-retrofit) | Type-K thermocouple → PID ramp/soak → heatwork & pyrometric cones. |

You are here: **coopilot**.
