const sky = document.querySelector('#sky');
const ctx = sky.getContext('2d');
const els = {
  weather: document.querySelector('#weather'),
  days: document.querySelector('#days'),
  meters: document.querySelector('#meters'),
  warn: document.querySelector('#warn'),
  outcome: document.querySelector('#outcome'),
  scene: document.querySelector('#scene'),
  choices: document.querySelector('#choices'),
  ending: document.querySelector('#ending'),
  fly: document.querySelector('#fly-line'),
  note: document.querySelector('#sound-note'),
  ai: document.querySelector('#use-ai'),
  voice: document.querySelector('#use-voice'),
  sounds: document.querySelector('#use-sounds'),
  restart: document.querySelector('#restart'),
};

const LABELS = {
  cautious: ['Safe', 'Fixes the nest'],
  clever: ['Clever', 'Finds food'],
  bold: ['Risky', 'A gamble: big meal or damage'],
};

let world = { period: 'day', raining: false, wind: 8 };
let busy = false;
let locked = false;
const eagle = { x: 180, y: 90 };
const pointer = { x: 180, y: 90, on: false };
const keys = new Set();
let zone = null;
let pending = null;
let view = { width: 800, height: 360 };

function resize() {
  const width = sky.clientWidth || 800;
  const height = 360;
  const dpr = window.devicePixelRatio || 1;
  if (sky.width !== Math.floor(width * dpr) || sky.height !== Math.floor(height * dpr)) {
    sky.width = Math.floor(width * dpr);
    sky.height = Math.floor(height * dpr);
  }
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  view = { width, height };
}

function zoneAt(x, y) {
  const nest = { x: view.width * 0.66, y: view.height * 0.56, r: 74 };
  const boat = { x: view.width * 0.40, y: view.height * 0.78, r: 52 };
  const near = (spot) => Math.hypot(x - spot.x, y - spot.y) < spot.r;
  if (near(nest)) return 'cautious';
  if (near(boat)) return 'clever';
  if (y > view.height * 0.68) return 'bold';
  return null;
}

function paint(time) {
  resize();
  const { width, height } = view;
  const period = world.period || 'day';
  const top = period === 'dawn' ? '#f6d7a8' : period === 'day' ? '#8ecae6' : period === 'dusk' ? '#f4a261' : '#1d2a4a';
  const bottom = period === 'dawn' ? '#e7a16a' : period === 'day' ? '#d8f3dc' : period === 'dusk' ? '#5c4d7a' : '#121a16';
  let ax = 0;
  let ay = 0;
  if (keys.has('ArrowLeft') || keys.has('KeyA')) ax -= 1;
  if (keys.has('ArrowRight') || keys.has('KeyD')) ax += 1;
  if (keys.has('ArrowUp') || keys.has('KeyW')) ay -= 1;
  if (keys.has('ArrowDown') || keys.has('KeyS')) ay += 1;
  if (pointer.on) {
    ax += (pointer.x - eagle.x) * 0.045;
    ay += (pointer.y - eagle.y) * 0.045;
  }
  ax += Math.sin(time / 700) * 0.12;
  eagle.x = Math.max(28, Math.min(width - 28, eagle.x + ax * 4.2));
  eagle.y = Math.max(28, Math.min(height - 28, eagle.y + ay * 4.2));

  const nest = { x: width * 0.66, y: height * 0.56, r: 74, name: 'NEST · fix it' };
  const boat = { x: width * 0.40, y: height * 0.78, r: 52, name: 'BOAT · find food' };
  const riverY = height * 0.68;
  const near = (spot) => Math.hypot(eagle.x - spot.x, eagle.y - spot.y) < spot.r;
  if (near(nest)) zone = 'cautious';
  else if (near(boat)) zone = 'clever';
  else if (eagle.y > riverY) zone = 'bold';
  else zone = null;
  if (!locked && !busy && keys.has('Space')) land(zone);
  if (!locked && !busy && pending && zone === pending) land(pending);

  const grad = ctx.createLinearGradient(0, 0, 0, height);
  grad.addColorStop(0, top);
  grad.addColorStop(1, bottom);
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, width, height);
  if (world.raining) {
    ctx.strokeStyle = 'rgba(216,243,220,0.45)';
    ctx.lineWidth = 2;
    for (let i = 0; i < 18; i++) {
      const x = (i * 57 + time / 8) % width;
      ctx.beginPath();
      ctx.moveTo(x, (i * 40) % height);
      ctx.lineTo(x - 10, (i * 40) % height + 18);
      ctx.stroke();
    }
  }
  ctx.fillStyle = 'rgba(255,255,255,0.35)';
  const cloudX = ((time / 40) % (width + 160)) - 80;
  ctx.beginPath();
  ctx.ellipse(cloudX, 70, 54, 16, 0, 0, Math.PI * 2);
  ctx.ellipse(cloudX + 36, 64, 28, 12, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = '#214e3a';
  ctx.beginPath();
  ctx.moveTo(0, height * 0.62);
  ctx.quadraticCurveTo(width * 0.5, height * 0.5, width, height * 0.6);
  ctx.lineTo(width, height);
  ctx.lineTo(0, height);
  ctx.fill();
  ctx.fillStyle = '#3d8ea3';
  ctx.fillRect(0, riverY, width, height - riverY);
  ctx.strokeStyle = 'rgba(216,243,220,0.45)';
  for (let i = 0; i < 4; i++) {
    const y = riverY + 18 + i * 16;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.quadraticCurveTo(width * 0.5, y + Math.sin(time / 300 + i) * 4, width, y);
    ctx.stroke();
  }
  ctx.fillStyle = '#6b4632';
  ctx.fillRect(nest.x - 6, nest.y, 14, 70);
  ctx.fillStyle = '#1f6b45';
  ctx.beginPath();
  ctx.ellipse(nest.x, nest.y - 8, 70, 46, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = '#c4a574';
  ctx.beginPath();
  ctx.ellipse(nest.x, nest.y + 22, 36, 12, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.beginPath();
  ctx.moveTo(boat.x - 28, boat.y);
  ctx.lineTo(boat.x + 28, boat.y);
  ctx.lineTo(boat.x + 18, boat.y + 12);
  ctx.lineTo(boat.x - 18, boat.y + 12);
  ctx.fill();
  ctx.strokeStyle = '#fdf3e2';
  ctx.beginPath();
  ctx.moveTo(boat.x, boat.y);
  ctx.lineTo(boat.x, boat.y - 22);
  ctx.stroke();

  function ring(spot, active) {
    ctx.beginPath();
    ctx.arc(spot.x, spot.y, spot.r, 0, Math.PI * 2);
    ctx.strokeStyle = active ? '#ffe9b0' : 'rgba(253,243,226,0.55)';
    ctx.lineWidth = active ? 3 : 1.5;
    ctx.setLineDash([6, 5]);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = '#fdf3e2';
    ctx.font = '700 13px Manrope, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(spot.name, spot.x, spot.y - spot.r - 8);
  }
  ring(nest, zone === 'cautious');
  ring(boat, zone === 'clever');
  if (zone === 'bold') {
    ctx.strokeStyle = '#ffe9b0';
    ctx.lineWidth = 3;
    ctx.strokeRect(8, riverY + 4, width - 16, height - riverY - 12);
  }
  ctx.fillStyle = '#fdf3e2';
  ctx.font = '700 13px Manrope, sans-serif';
  ctx.textAlign = 'left';
  ctx.fillText('RIVER · a gamble', 16, riverY + 22);

  const flap = Math.sin(time / 90) * 10;
  ctx.save();
  ctx.translate(eagle.x, eagle.y);
  ctx.fillStyle = '#3e342c';
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
  ctx.fillStyle = '#ffcf7a';
  ctx.beginPath();
  ctx.arc(14, -1, 4, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();

  const hint = busy ? 'The river is answering...'
    : zone === 'cautious' ? 'Nest fixes the branches. Click or press space.'
    : zone === 'clever' ? 'Boat finds food. Click or press space.'
    : zone === 'bold' ? 'River is a gamble. Click or press space.'
    : 'Fly to the nest, the boat, or the river.';
  ctx.font = '600 15px Manrope, sans-serif';
  ctx.fillStyle = 'rgba(36,27,46,0.78)';
  ctx.fillRect(16, 16, ctx.measureText(hint).width + 28, 32);
  ctx.fillStyle = '#fdf3e2';
  ctx.textAlign = 'left';
  ctx.fillText(hint, 28, 38);
  requestAnimationFrame(paint);
}

function render(data) {
  const campus = data.campus || {};
  world = campus;
  const temp = campus.temp_f == null ? '' : `${campus.temp_f}°F · `;
  els.weather.textContent = `${campus.place}, on the ${campus.river} · ${campus.clock} · ${temp}${campus.summary} · wind ${campus.wind_mph} mph`;
  const day = Math.min(data.turn, 8);
  els.days.innerHTML = Array.from({ length: 8 }, (_, i) => {
    const n = i + 1;
    const cls = data.over ? (n < data.turn ? 'on' : '') : (n < day ? 'on' : n === day ? 'now' : '');
    return `<i class="pip ${cls}"></i>`;
  }).join('') + `<span>Day ${Math.min(day, 8)} of 8</span>`;
  els.meters.innerHTML = [
    ['Nest health', data.health, 'health'],
    ['Food', data.food, 'food'],
  ].map(([name, value, cls]) => (
    `<div class="meter"><header><span>${name}</span><span>${value}/10</span></header>`
    + `<div class="track"><div class="fill ${cls}" style="width:${value * 10}%"></div></div></div>`
  )).join('');
  const worry = [];
  if (data.health <= 3) worry.push('the branches are failing');
  if (data.food <= 3) worry.push('the chicks are hungry');
  els.warn.hidden = worry.length === 0 || data.over;
  els.warn.textContent = worry.length ? `Watch the bars. Right now ${worry.join(' and ')}.` : '';
  els.outcome.hidden = !data.outcome;
  els.outcome.textContent = data.outcome || '';
  if (data.over) {
    showEnding(data);
    return;
  }
  locked = false;
  els.ending.hidden = true;
  sky.hidden = false;
  els.fly.hidden = false;
  els.choices.hidden = false;
  els.scene.hidden = false;
  const scene = data.scene;
  const dayNo = data.turn;
  const talk = scene.dialogue
    ? `<div class="dialogue"><span class="who">${escape(scene.dialogue.speaker)}</span><span>${escape(scene.dialogue.line)}</span></div>`
    : '';
  els.scene.innerHTML = `<div class="kicker">Day ${dayNo}</div><p class="narration">${escape(scene.narration)}</p>${talk}`;
  els.choices.innerHTML = scene.choices.map((choice) => {
    const [label, effect] = LABELS[choice.kind];
    return `<div class="choice"><span class="tag ${choice.kind}">${label} · ${effect}</span>`
      + `<button type="button" data-kind="${choice.kind}">${escape(choice.text)}</button></div>`;
  }).join('');
  if (data.audio && els.voice.checked) {
    const player = new Audio(data.audio);
    player.play().catch(() => {});
  }
}

function showEnding(data) {
  locked = true;
  sky.hidden = true;
  els.fly.hidden = true;
  els.choices.hidden = true;
  els.scene.hidden = true;
  els.ending.hidden = false;
  const banner = data.won
    ? `<div class="banner won"><h2>The chicks fledged.</h2><p class="score">${data.score}</p><p>Nest health and food, still holding on day eight.</p></div>`
    : '<div class="banner lost"><h2>The nest was lost.</h2><p>The river is still there. The next story can end differently.</p></div>';
  const ending = data.ending ? `<p class="narration">${escape(data.ending)}</p>` : '';
  const log = (data.log || []).map((row) => (
    `<div class="log"><strong>Day ${row.turn}.</strong> ${escape(row.choice)} — ${escape(row.outcome)}</div>`
  )).join('');
  els.ending.innerHTML = banner + ending + '<h3>The days you flew</h3>' + log;
  if (data.audio && els.voice.checked) new Audio(data.audio).play().catch(() => {});
}

function escape(text) {
  return String(text).replace(/[&<>"']/g, (ch) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[ch]));
}

async function call(path, extra) {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      use_ai: els.ai.checked,
      use_voice: els.voice.checked,
      ...extra,
    }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'The nest could not answer.');
  return data;
}

async function begin() {
  busy = true;
  els.scene.classList.add('busy');
  els.scene.innerHTML = '<p class="narration">The sun rises over the nest...</p>';
  try {
    render(await call('/api/start'));
  } catch (err) {
    els.scene.innerHTML = `<p class="narration">${escape(err.message)}</p>`;
  } finally {
    busy = false;
    els.scene.classList.remove('busy');
  }
}

async function land(kind) {
  if (!kind || busy || locked) return;
  busy = true;
  pending = null;
  els.scene.classList.add('busy');
  document.querySelectorAll('#choices button').forEach((button) => { button.disabled = true; });
  try {
    render(await call('/api/choose', { kind }));
  } catch (err) {
    els.outcome.hidden = false;
    els.outcome.textContent = err.message;
  } finally {
    busy = false;
    els.scene.classList.remove('busy');
    document.querySelectorAll('#choices button').forEach((button) => { button.disabled = false; });
  }
}

function aim(event) {
  const rect = sky.getBoundingClientRect();
  pointer.x = event.clientX - rect.left;
  pointer.y = event.clientY - rect.top;
  pointer.on = true;
}

sky.addEventListener('pointermove', aim);
sky.addEventListener('pointerdown', (event) => {
  aim(event);
  sky.focus();
  armSounds();
  pending = zoneAt(pointer.x, pointer.y);
  if (pending && zone === pending) land(pending);
});
sky.addEventListener('pointerleave', () => { pointer.on = false; });
window.addEventListener('keydown', (event) => {
  const fly = ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'KeyA', 'KeyD', 'KeyW', 'KeyS', 'Space'];
  if (fly.includes(event.code)) {
    event.preventDefault();
    keys.add(event.code);
    armSounds();
  }
  if (event.code === 'Digit1') land('cautious');
  if (event.code === 'Digit2') land('clever');
  if (event.code === 'Digit3') land('bold');
});
window.addEventListener('keyup', (event) => keys.delete(event.code));
els.choices.addEventListener('click', (event) => {
  const button = event.target.closest('button');
  if (button) land(button.dataset.kind);
});
els.restart.addEventListener('click', begin);

const bag = { ctx: null, nodes: null };
function chirp() {
  if (!bag.ctx || bag.ctx.state !== 'running' || !els.sounds.checked) return;
  const now = bag.ctx.currentTime;
  const osc = bag.ctx.createOscillator();
  const gain = bag.ctx.createGain();
  osc.type = 'sine';
  osc.frequency.setValueAtTime(1900 + Math.random() * 400, now);
  osc.frequency.exponentialRampToValueAtTime(2800 + Math.random() * 500, now + 0.09);
  gain.gain.setValueAtTime(0.0001, now);
  gain.gain.exponentialRampToValueAtTime(0.04, now + 0.02);
  gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.16);
  osc.connect(gain).connect(bag.ctx.destination);
  osc.start(now);
  osc.stop(now + 0.18);
}
function armSounds() {
  if (!els.sounds.checked) return;
  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  if (!AudioCtx) return;
  const wind = Math.max(4, Math.min(20, world.wind || 8));
  if (!bag.ctx) bag.ctx = new AudioCtx();
  if (bag.ctx.state === 'suspended') bag.ctx.resume();
  if (bag.nodes) {
    bag.nodes.wind.gain.value = 0.03 + wind / 180;
    els.note.textContent = 'You can hear the Huron River, the wind, and a bird.';
    return;
  }
  const rate = bag.ctx.sampleRate;
  const buffer = bag.ctx.createBuffer(1, rate * 2, rate);
  const samples = buffer.getChannelData(0);
  let brown = 0;
  for (let i = 0; i < samples.length; i++) {
    const white = Math.random() * 2 - 1;
    brown = (brown + 0.02 * white) / 1.02;
    samples[i] = brown * 3.5;
  }
  function layer(type, frequency, amount) {
    const source = bag.ctx.createBufferSource();
    source.buffer = buffer;
    source.loop = true;
    const filter = bag.ctx.createBiquadFilter();
    filter.type = type;
    filter.frequency.value = frequency;
    const gain = bag.ctx.createGain();
    gain.gain.value = amount;
    source.connect(filter).connect(gain).connect(bag.ctx.destination);
    source.start();
    return gain;
  }
  bag.nodes = {
    river: layer('lowpass', 280, 0.16),
    wind: layer('bandpass', 700, 0.03 + wind / 180),
  };
  setInterval(chirp, 2800);
  chirp();
  els.note.textContent = 'You can hear the Huron River, the wind, and a bird.';
}

requestAnimationFrame(paint);
begin();
