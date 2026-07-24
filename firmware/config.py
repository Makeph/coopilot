# config.py -- everything you tune for the coop controller lives here.
#
# Units: temperature in Celsius, humidity in %RH, weights in %, time in seconds,
# current in amperes. The door safety logic in door.py runs fully offline; WiFi
# and MQTT below are optional and only add the dashboard feed and remote view.

# ---------------------------------------------------------------------------
# WiFi + MQTT (optional). The door opens and closes without any of this.
# ---------------------------------------------------------------------------
WIFI_SSID = ""
WIFI_PASS = ""
MQTT_BROKER = ""               # e.g. "192.168.1.20"; empty = telemetry disabled
MQTT_PORT = 1883
MQTT_PREFIX = "coop"           # topics: coop/climate, coop/door/state, ...

# ---------------------------------------------------------------------------
# GPIO pin map (ESP32 defaults). Change to match your wiring.
# ---------------------------------------------------------------------------
PIN_MOTOR_OPEN  = 25           # H-bridge IN1 (drive door open)
PIN_MOTOR_CLOSE = 26           # H-bridge IN2 (drive door close)
PIN_LIMIT_OPEN  = 32           # limit switch: door fully open   (active-low, pull-up)
PIN_LIMIT_CLOSED = 33          # limit switch: door fully closed (active-low, pull-up)
PIN_IR_BEAM     = 27           # obstacle/anti-pinch beam (active-low when broken)
PIN_MOTOR_CURRENT = 35         # ADC: motor current sense (for overcurrent)

I2C_SCL = 22                   # BME280 climate sensor
I2C_SDA = 21
PIN_HX711_WATER_DT = 16        # water tank load cell
PIN_HX711_WATER_SCK = 17
PIN_HX711_FOOD_DT = 18         # feeder load cell
PIN_HX711_FOOD_SCK = 19

# ---------------------------------------------------------------------------
# DOOR SAFETY (all enforced locally by door.py)
# ---------------------------------------------------------------------------
MOVE_TIMEOUT_S      = 15       # a full open/close must reach its limit within this
MOTOR_OVERCURRENT_A = 2.5      # above this the motor is stalled/jammed -> fault
MOTOR_CURRENT_FS_A  = 5.0      # current-sense full-scale (amps at ADC max)
# The IR beam and both limit switches are wired active-low with internal pull-ups.
LIMIT_ACTIVE_LOW = True
IR_ACTIVE_LOW    = True

# ---------------------------------------------------------------------------
# AUTOMATIC SCHEDULE (offline uptime clock is fine; NTP only sharpens it)
# ---------------------------------------------------------------------------
TIMEZONE_OFFSET_H = 1
DOOR_OPEN_H  = 7               # auto-open at 07:00
DOOR_CLOSE_H = 21             # auto-close at 21:00

# ---------------------------------------------------------------------------
# RESOURCES + CLIMATE alerts
# ---------------------------------------------------------------------------
WATER_LOW_PCT = 20             # below this -> low-water alert
FOOD_LOW_PCT  = 15             # below this -> low-food alert
TEMP_LOW_C    = -5             # freezing risk alert
TEMP_HIGH_C   = 32             # heat-stress alert

# ---------------------------------------------------------------------------
# Loop timing
# ---------------------------------------------------------------------------
SENSE_INTERVAL_S = 5
