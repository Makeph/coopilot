// app.js -- drives the dashboard from the CoopSim (sim.js). Live-updating, no
// backend. The door-safety rules shown here mirror the firmware (firmware/door.py),
// which is exhaustively unit-tested. Swap CoopSim for a real MQTT-over-WebSocket
// feed to go from demo to production without touching the render code.

const sim = new CoopSim();
const $ = (s) => document.querySelector(s);

const DOOR_LABEL = {
  closed: "Fermée", open: "Ouverte",
  opening: "Ouverture…", closing: "Fermeture…", fault: "Défaut",
};
const ALERT_LABEL = {
  water_low: "Niveau d'eau bas", food_low: "Réserve de nourriture basse",
  temp_low: "Risque de gel", temp_high: "Chaleur excessive",
};

const toast = (msg) => {
  if (!msg) return;
  const el = $("#toast");
  el.textContent = msg;
  el.classList.add("show");
  window.setTimeout(() => el.classList.remove("show"), 2600);
};

$("#today").textContent = new Intl.DateTimeFormat("fr-FR", {
  weekday: "long", day: "numeric", month: "long",
}).format(new Date());

const isOpenish = () => sim.door === "open" || sim.door === "opening";

function render(s) {
  $("#temperature").textContent = s.temperature_c.toFixed(1).replace(".", ",");
  $("#humidity").textContent = s.humidity_pct;

  $("#water-value").textContent = s.water_pct + " %";
  $("#food-value").textContent = s.food_pct + " %";
  $("#water-meter").style.width = s.water_pct + "%";
  $("#food-meter").style.width = s.food_pct + "%";

  const open = s.door === "open" || s.door === "opening";
  const moving = s.door === "opening" || s.door === "closing";
  $("#door-state").textContent = DOOR_LABEL[s.door] || s.door;
  $("#door-state").className = "state " + (s.door === "fault" ? "bad" : "good");
  $("#door-graphic").classList.toggle("open", open);
  $("#door-action").textContent = open ? "Fermer la porte" : "Ouvrir la porte";
  $("#door-action").disabled = moving || s.door === "fault";

  const obs = $("#obstacle-toggle");
  if (obs) {
    obs.textContent = s.obstacle ? "🐔 Passage bloqué" : "Passage libre";
    obs.classList.toggle("active", s.obstacle);
  }

  const strip = $(".alert-strip");
  if (s.alerts.length) {
    strip.style.display = "";
    strip.querySelector("strong").textContent =
      s.alerts.length + (s.alerts.length > 1 ? " points d'attention" : " point d'attention");
    strip.querySelector("span").textContent = s.alerts.map((a) => ALERT_LABEL[a] || a).join(" · ");
  } else {
    strip.style.display = "none";
  }

  $(".connection strong").textContent = s.device_online ? "ESP32 connecté" : "ESP32 hors ligne";
}

// --- manual door command (with the safety confirmation) -----------------
$("#door-action").addEventListener("click", () => {
  const open = isOpenish();
  $("#dialog-title").textContent = open ? "Fermer la porte ?" : "Ouvrir la porte ?";
  $("#dialog-copy").textContent = open
    ? "Vérifiez qu'aucune poule ne se trouve dans le passage. Le capteur anti-pincement reste actif."
    : "La porte va s'ouvrir immédiatement et le programme automatique reprendra au prochain horaire.";
  $("#confirm-dialog").showModal();
});
$("#confirm-dialog").addEventListener("close", (event) => {
  if (event.target.returnValue !== "confirm") return;
  toast(sim.command(isOpenish() ? "close" : "open"));
  render(sim.snapshot());
});

$("#refresh").addEventListener("click", () => { render(sim.snapshot()); toast("Mesures à jour."); });
$("#refill-all").addEventListener("click", () => { sim.refill(); render(sim.snapshot()); toast("Réserves remplies."); });
$("#health-log").addEventListener("click", () => {
  const note = window.prompt("Observation à ajouter au carnet de santé :");
  if (note?.trim()) toast("Observation enregistrée localement.");
});

// Obstacle demo toggle: flip it, then press "Fermer" (refused) or catch a close
// mid-travel to watch the anti-pinch reopen -- the same rule the firmware enforces.
$("#obstacle-toggle")?.addEventListener("click", () => {
  sim.obstacle = !sim.obstacle;
  toast(sim.obstacle ? "Obstacle simulé dans le passage." : "Passage dégagé.");
  render(sim.snapshot());
});

$("[data-scroll='water']").addEventListener("click", () =>
  $("#water").scrollIntoView({ behavior: "smooth", block: "center" }));
document.querySelectorAll(".nav-item").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".nav-item").forEach((i) => i.classList.remove("active"));
    button.classList.add("active");
    const targets = { door: ".door-panel", resources: ".resources-panel", health: ".health-panel" };
    if (targets[button.dataset.view]) {
      $(targets[button.dataset.view]).scrollIntoView({ behavior: "smooth", block: "start" });
    } else if (button.dataset.view === "settings") {
      toast("Les réglages matériels arrivent dans une prochaine étape.");
    } else {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  });
});

// Live loop: 1 real second = 1 simulated minute, so the climate drifts and the
// reserves deplete visibly during a demo.
render(sim.tick(0));
window.setInterval(() => render(sim.tick(60_000)), 1000);
