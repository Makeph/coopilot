// sim.js -- a browser-side simulation of the coop that mirrors the firmware's
// data contract and door-safety behaviour, so the dashboard runs as a live demo
// with evolving data and a working (simulated) door -- no hardware, no broker.
//
// The door logic here intentionally mirrors firmware/door.py: a close reverses
// on an obstacle (anti-pinch) and refuses to start while the passage is blocked.
// The same rules are exhaustively unit-tested on the firmware side.

const MOVE_MS = 3000; // simulated full open/close travel time

class CoopSim {
  constructor() {
    this.t = 0; // ms of sim time
    this.temperature = 18.6;
    this.humidity = 61;
    this.water = 32;
    this.food = 68;
    this.door = "open"; // closed | open | opening | closing | fault
    this.obstacle = false;
    this._moveStart = 0;
    this._lastReason = "";
  }

  // --- commands (what the dashboard button triggers) ---------------------
  command(cmd) {
    if (cmd === "open") {
      if (this.door === "open" || this.door === "opening") return "Déjà ouverte.";
      this.door = "opening";
      this._moveStart = this.t;
      return (this._lastReason = "Ouverture en cours…");
    }
    if (cmd === "close") {
      if (this.door === "closed" || this.door === "closing") return "Déjà fermée.";
      if (this.obstacle) return (this._lastReason = "Fermeture refusée : passage bloqué.");
      this.door = "closing";
      this._moveStart = this.t;
      return (this._lastReason = "Fermeture en cours…");
    }
    return "";
  }

  refill() {
    this.water = 100;
    this.food = 100;
  }

  // --- evolution --------------------------------------------------------
  tick(dtMs) {
    this.t += dtMs;
    const dtH = dtMs / 3_600_000;

    // Diurnal climate: a gentle sine over a 24 h day plus a little noise.
    const hourOfDay = (this.t / 3_600_000) % 24;
    const base = 17 + 5 * Math.sin(((hourOfDay - 9) / 24) * 2 * Math.PI);
    this.temperature = clamp(base + (Math.random() - 0.5) * 0.6, 2, 34);
    this.humidity = Math.round(clamp(72 - (this.temperature - 15) * 1.4 + (Math.random() - 0.5) * 3, 45, 85));

    // Resources deplete slowly (accelerated so a demo actually moves).
    this.water = clamp(this.water - dtH * 18, 0, 100);
    this.food = clamp(this.food - dtH * 6, 0, 100);

    // Door travel + anti-pinch.
    if (this.door === "closing") {
      if (this.obstacle) {
        this.door = "opening"; // reverse to open (anti-pinch)
        this._moveStart = this.t;
        this._lastReason = "Obstacle détecté : réouverture (anti-pincement).";
      } else if (this.t - this._moveStart >= MOVE_MS) {
        this.door = "closed";
        this._lastReason = "Porte fermée.";
      }
    } else if (this.door === "opening") {
      if (this.t - this._moveStart >= MOVE_MS) {
        this.door = "open";
        this._lastReason = "Porte ouverte.";
      }
    }
    return this.snapshot();
  }

  lastReason() {
    return this._lastReason;
  }

  // Matches the README's MQTT data contract.
  snapshot() {
    return {
      timestamp: new Date().toISOString(),
      temperature_c: round1(this.temperature),
      humidity_pct: Math.round(this.humidity),
      water_pct: Math.round(this.water),
      food_pct: Math.round(this.food),
      door: this.door,
      obstacle: this.obstacle,
      device_online: true,
      alerts: this._alerts(),
    };
  }

  _alerts() {
    const a = [];
    if (this.water < 20) a.push("water_low");
    if (this.food < 15) a.push("food_low");
    if (this.temperature < -5) a.push("temp_low");
    if (this.temperature > 32) a.push("temp_high");
    return a;
  }
}

function clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v));
}
function round1(v) {
  return Math.round(v * 10) / 10;
}
