import streamlit as st

_FLIGHT = st.components.v2.component(
    'nest_flight',
    isolate_styles=True,
    js=r"""
export default function(component) {
  const { setTriggerValue, parentElement, data } = component;
  if (parentElement._stop) parentElement._stop();

  const canvas = document.createElement("canvas");
  canvas.style.width = "100%";
  canvas.style.height = "360px";
  canvas.style.display = "block";
  canvas.style.borderRadius = "22px";
  canvas.style.cursor = "crosshair";
  canvas.tabIndex = 0;
  parentElement.appendChild(canvas);
  const ctx = canvas.getContext("2d");

  const keys = new Set();
  const eagle = { x: 180, y: 90 };
  const pointer = { x: 180, y: 90, on: false };
  let zone = null;
  let sent = false;
  let pending = null;
  let view = { width: 800, height: 360 };

  function zoneAt(x, y) {
    const nest = { x: view.width * 0.66, y: view.height * 0.56, r: 74 };
    const boat = { x: view.width * 0.40, y: view.height * 0.78, r: 52 };
    const near = (spot) => Math.hypot(x - spot.x, y - spot.y) < spot.r;
    if (near(nest)) return "cautious";
    if (near(boat)) return "clever";
    if (y > view.height * 0.68) return "bold";
    return null;
  }
  let raf = 0;

  function world() {
    const width = canvas.clientWidth || 800;
    const height = 360;
    const dpr = window.devicePixelRatio || 1;
    if (canvas.width !== Math.floor(width * dpr) || canvas.height !== Math.floor(height * dpr)) {
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { width, height };
  }

  function onKey(event) {
    const fly = ["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "KeyA", "KeyD", "KeyW", "KeyS", "Space"];
    if (!fly.includes(event.code)) return;
    event.preventDefault();
    if (event.type === "keydown") keys.add(event.code);
    else keys.delete(event.code);
  }

  function aim(event) {
    const rect = canvas.getBoundingClientRect();
    pointer.x = event.clientX - rect.left;
    pointer.y = event.clientY - rect.top;
    pointer.on = true;
  }

  function commit() {
    if (sent || !zone) return;
    sent = true;
    setTriggerValue("landed", zone);
  }

  window.addEventListener("keydown", onKey);
  window.addEventListener("keyup", onKey);
  canvas.addEventListener("pointermove", aim);
  canvas.addEventListener("pointerdown", (event) => {
    aim(event);
    pending = zoneAt(pointer.x, pointer.y);
    if (pending && zone === pending) commit();
  });
  canvas.addEventListener("pointerleave", () => { pointer.on = false; });

  function frame(time) {
    const { width, height } = world();
    view = { width, height };
    const period = (data && data.period) || "day";
    const raining = data && data.raining;
    const top = period === "dawn" ? "#f6d7a8" : period === "day" ? "#8ecae6" : period === "dusk" ? "#f4a261" : "#1d2a4a";
    const bottom = period === "dawn" ? "#e7a16a" : period === "day" ? "#d8f3dc" : period === "dusk" ? "#5c4d7a" : "#121a16";

    let ax = 0;
    let ay = 0;
    if (keys.has("ArrowLeft") || keys.has("KeyA")) ax -= 1;
    if (keys.has("ArrowRight") || keys.has("KeyD")) ax += 1;
    if (keys.has("ArrowUp") || keys.has("KeyW")) ay -= 1;
    if (keys.has("ArrowDown") || keys.has("KeyS")) ay += 1;
    if (pointer.on) {
      ax += (pointer.x - eagle.x) * 0.045;
      ay += (pointer.y - eagle.y) * 0.045;
    }
    ax += Math.sin(time / 700) * 0.12;
    eagle.x = Math.max(28, Math.min(width - 28, eagle.x + ax * 4.2));
    eagle.y = Math.max(28, Math.min(height - 28, eagle.y + ay * 4.2));

    const nest = { x: width * 0.66, y: height * 0.56, r: 74, kind: "cautious", name: "NEST · fix it" };
    const boat = { x: width * 0.40, y: height * 0.78, r: 52, kind: "clever", name: "BOAT · find food" };
    const riverY = height * 0.68;
    const near = (spot) => Math.hypot(eagle.x - spot.x, eagle.y - spot.y) < spot.r;
    if (near(nest)) zone = "cautious";
    else if (near(boat)) zone = "clever";
    else if (eagle.y > riverY) zone = "bold";
    else zone = null;
    if (keys.has("Space")) commit();
    if (pending && zone === pending) commit();

    const sky = ctx.createLinearGradient(0, 0, 0, height);
    sky.addColorStop(0, top);
    sky.addColorStop(1, bottom);
    ctx.fillStyle = sky;
    ctx.fillRect(0, 0, width, height);
    if (raining) {
      ctx.strokeStyle = "rgba(216,243,220,0.45)";
      ctx.lineWidth = 2;
      for (let i = 0; i < 18; i++) {
        const x = (i * 57 + time / 8) % width;
        ctx.beginPath();
        ctx.moveTo(x, (i * 40) % height);
        ctx.lineTo(x - 10, (i * 40) % height + 18);
        ctx.stroke();
      }
    }

    ctx.fillStyle = "rgba(255,255,255,0.35)";
    const cloudX = ((time / 40) % (width + 160)) - 80;
    ctx.beginPath();
    ctx.ellipse(cloudX, 70, 54, 16, 0, 0, Math.PI * 2);
    ctx.ellipse(cloudX + 36, 64, 28, 12, 0, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = "#214e3a";
    ctx.beginPath();
    ctx.moveTo(0, height * 0.62);
    ctx.quadraticCurveTo(width * 0.5, height * 0.5, width, height * 0.6);
    ctx.lineTo(width, height);
    ctx.lineTo(0, height);
    ctx.fill();

    ctx.fillStyle = "#3d8ea3";
    ctx.fillRect(0, riverY, width, height - riverY);
    ctx.strokeStyle = "rgba(216,243,220,0.45)";
    ctx.lineWidth = 2;
    for (let i = 0; i < 4; i++) {
      const y = riverY + 18 + i * 16;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.quadraticCurveTo(width * 0.5, y + Math.sin(time / 300 + i) * 4, width, y);
      ctx.stroke();
    }

    ctx.fillStyle = "#6b4632";
    ctx.fillRect(nest.x - 6, nest.y, 14, 70);
    ctx.fillStyle = "#1f6b45";
    ctx.beginPath();
    ctx.ellipse(nest.x, nest.y - 8, 70, 46, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#c4a574";
    ctx.beginPath();
    ctx.ellipse(nest.x, nest.y + 22, 36, 12, 0, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = "#c4a574";
    ctx.beginPath();
    ctx.moveTo(boat.x - 28, boat.y);
    ctx.lineTo(boat.x + 28, boat.y);
    ctx.lineTo(boat.x + 18, boat.y + 12);
    ctx.lineTo(boat.x - 18, boat.y + 12);
    ctx.fill();
    ctx.strokeStyle = "#f6f1e6";
    ctx.beginPath();
    ctx.moveTo(boat.x, boat.y);
    ctx.lineTo(boat.x, boat.y - 22);
    ctx.stroke();

    function ring(spot, active) {
      ctx.beginPath();
      ctx.arc(spot.x, spot.y, spot.r, 0, Math.PI * 2);
      ctx.strokeStyle = active ? "#f6f1e6" : "rgba(246,241,230,0.45)";
      ctx.lineWidth = active ? 3 : 1.5;
      ctx.setLineDash([6, 5]);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = "#f6f1e6";
      ctx.font = "700 13px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(spot.name, spot.x, spot.y - spot.r - 8);
    }
    ring(nest, zone === "cautious");
    ring(boat, zone === "clever");
    if (zone === "bold") {
      ctx.strokeStyle = "#f6f1e6";
      ctx.lineWidth = 3;
      ctx.strokeRect(8, riverY + 4, width - 16, height - riverY - 12);
    }
    ctx.fillStyle = "#f6f1e6";
    ctx.font = "700 13px sans-serif";
    ctx.textAlign = "left";
    ctx.fillText("RIVER · a gamble", 16, riverY + 22);

    const flap = Math.sin(time / 90) * 10;
    ctx.save();
    ctx.translate(eagle.x, eagle.y);
    ctx.fillStyle = "#3e342c";
    ctx.beginPath();
    ctx.moveTo(-6, 0);
    ctx.quadraticCurveTo(-28, -18 - flap, -46, -2);
    ctx.quadraticCurveTo(-20, 6, -6, 3);
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(6, 0);
    ctx.quadraticCurveTo(28, -18 - flap, 46, -2);
    ctx.quadraticCurveTo(20, 6, 6, 3);
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(0, 0, 16, 7, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#f4d58d";
    ctx.beginPath();
    ctx.arc(14, -1, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    const hint = zone === "cautious" ? "Nest fixes the branches. Click or press space."
      : zone === "clever" ? "Boat finds food. Click or press space."
      : zone === "bold" ? "River is a gamble. Click or press space."
      : "Fly to the nest, the boat, or the river.";
    ctx.font = "600 15px sans-serif";
    ctx.fillStyle = "rgba(20,33,28,0.72)";
    ctx.fillRect(16, 16, ctx.measureText(hint).width + 28, 32);
    ctx.fillStyle = "#f6f1e6";
    ctx.font = "600 15px sans-serif";
    ctx.textAlign = "left";
    ctx.fillText(hint, 28, 38);

    raf = requestAnimationFrame(frame);
  }

  raf = requestAnimationFrame(frame);
  canvas.focus();
  parentElement._stop = () => {
    cancelAnimationFrame(raf);
    window.removeEventListener("keydown", onKey);
    window.removeEventListener("keyup", onKey);
  };
}
""",
)


def flight_canvas(turn, health, food, period='day', raining=False, wind=8):
    """A live scene. Returns the zone the player landed in, once."""
    result = _FLIGHT(
        key=f'flight-{turn}',
        data={'turn': turn, 'health': health, 'food': food, 'period': period, 'raining': raining, 'wind': wind},
        height=360,
        on_landed_change=lambda: None,
    )
    landed = result['landed'] if result is not None and 'landed' in result else None
    return landed if landed in ('cautious', 'bold', 'clever') else None
