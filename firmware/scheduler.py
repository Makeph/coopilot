# scheduler.py -- wall-clock hour for the autonomous daily door schedule.
# If WiFi is up we NTP-sync the RTC. Offline, local_hour() returns None and the
# door simply holds its last position until commanded -- it never guesses.
import time
import config

try:
    import ntptime
except ImportError:
    ntptime = None


def sync_clock():
    if ntptime is None:
        return False
    try:
        ntptime.settime()  # sets the RTC to UTC
        return True
    except Exception as e:
        print("scheduler: ntp sync failed:", e)
        return False


def _valid(tm):
    # Before any NTP sync the epoch year is 1970/2000; treat that as "no clock".
    return tm is not None and tm[0] >= 2021


def local_hour():
    try:
        tm = time.localtime(time.time() + int(config.TIMEZONE_OFFSET_H * 3600))
    except Exception:
        return None
    return tm[3] if _valid(tm) else None


def scheduled_command(hour):
    """Autonomous daily schedule: open during the day, close at night, or None
    while the clock is unset (so the door holds position)."""
    if hour is None:
        return None
    day = config.DOOR_OPEN_H <= hour < config.DOOR_CLOSE_H
    return "open" if day else "close"
