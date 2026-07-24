# boot.py -- best-effort WiFi bring-up. The coop controller runs fully without it;
# WiFi only enables NTP time (for the daily schedule) and MQTT telemetry.
import time
import config

_wifi_ok = False


def _connect():
    global _wifi_ok
    if not config.WIFI_SSID:
        return
    try:
        import network
        sta = network.WLAN(network.STA_IF)
        sta.active(True)
        if not sta.isconnected():
            sta.connect(config.WIFI_SSID, config.WIFI_PASS)
            deadline = time.ticks_add(time.ticks_ms(), 15000)
            while not sta.isconnected():
                if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                    print("boot: wifi timeout, running offline")
                    return
                time.sleep_ms(250)
        _wifi_ok = True
        print("boot: wifi up", sta.ifconfig()[0])
    except Exception as e:
        print("boot: wifi error:", e)


def wifi_ok():
    return _wifi_ok


_connect()
