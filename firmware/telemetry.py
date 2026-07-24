# telemetry.py -- best-effort MQTT publish of coop state, matching the topic
# contract in the README. Entirely optional: with no broker configured (or the
# umqtt library missing) this is a no-op and the controller runs unchanged.
import config

try:
    from umqtt.simple import MQTTClient
except ImportError:
    MQTTClient = None


class Telemetry:
    def __init__(self):
        self._c = None
        if MQTTClient and config.MQTT_BROKER:
            try:
                self._c = MQTTClient(b"coopilot", config.MQTT_BROKER, config.MQTT_PORT)
                self._c.connect()
                print("telemetry: mqtt connected")
            except Exception as e:
                print("telemetry: connect failed:", e)
                self._c = None

    def publish(self, state):
        if self._c is None:
            return
        import json
        p = config.MQTT_PREFIX
        try:
            self._c.publish(p + "/climate", json.dumps({
                "temperature_c": state.get("temperature_c"),
                "humidity_pct": state.get("humidity_pct"),
            }))
            self._c.publish(p + "/resources", json.dumps({
                "water_pct": state.get("water_pct"),
                "food_pct": state.get("food_pct"),
            }))
            self._c.publish(p + "/door/state", state.get("door", "unknown"))
            if state.get("alerts"):
                self._c.publish(p + "/alerts", json.dumps(state["alerts"]))
        except Exception as e:
            print("telemetry: publish failed:", e)
