const sky = document.querySelector('#sky');
const ctx = sky.getContext('2d');
const nextDay = document.querySelector('#next-day');
const els = {
  weather: document.querySelector('#weather'),
  days: document.querySelector('#days'),
  meters: document.querySelector('#meters'),
  warn: document.querySelector('#warn'),
  outcome: document.querySelector('#outcome'),
  scene: document.querySelector('#scene'),
  ending: document.querySelector('#ending'),
  fly: document.querySelector('#fly-line'),
  note: document.querySelector('#sound-note'),
  ai: document.querySelector('#use-ai'),
  voice: document.querySelector('#use-voice'),
  sounds: document.querySelector('#use-sounds'),
  restart: document.querySelector('#restart'),
};

const FLIGHT_MS = 20000;
let world = { period: 'day', raining: false, wind: 8 };
let mode = 'wait';
let flight = null;
let landing = false;
let view = { width: 800, height: 420 };
const keys = new Set();
const pointer = { y: 180, on: false };

function resize() {
  const width = sky.clientWidth || 800;
  const height = 420;
  const dpr = window.devicePixelRatio || 1;
  if (sky.width !== Math.floor(width * dpr) || sky.height !== Math.floor(height * dpr)) {
    sky.width = Math.floor(width * dpr);
    sky.height = Math.floor(height * dpr);
  }
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  view = { width, height };
}

function renderHud(data) {
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
}

function showStory(data) {
  renderHud(data);
  els.outcome.hidden = !data.outcome;
  els.outcome.textContent = data.outcome || '';
  if (data.over) {
    showEnding(data);
    return;
  }
  const scene = data.scene;
  const dayNo = data.turn - 1;
  const talk = scene && scene.dialogue
    ? `<div class="dialogue"><span class="who">${escape(scene.dialogue.speaker)}</span><span>${escape(scene.dialogue.line)}</span></div>`
    : '';
  els.scene.hidden = false;
  els.scene.classList.remove('busy');
  els.scene.innerHTML = `<div class="kicker">Day ${dayNo}</div><p class="narration">${escape(scene.narration)}</p>${talk}`;
  els.ending.hidden = true;
  sky.hidden = false;
  els.fly.hidden = false;
  nextDay.hidden = false;
  nextDay.textContent = `Fly day ${data.turn}`;
  playVoice();
}

function showEnding(data) {
  mode = 'over';
  flight = null;
  sky.hidden = true;
  els.fly.hidden = true;
  nextDay.hidden = true;
  els.scene.hidden = true;
  els.ending.hidden = false;
  const banner = data.won
    ? `<div class="banner won"><h2>The chicks fledged.</h2><p class="score">${data.score}</p><p>Nest health and food, still holding after eight flights.</p></div>`
    : '<div class="banner lost"><h2>The nest was lost.</h2><p>The river is still there. The next story can end differently.</p></div>';
  const ending = data.ending ? `<p class="narration">${escape(data.ending)}</p>` : '';
  const log = (data.log || []).map((row) => (
    `<div class="log"><strong>Day ${row.turn}.</strong> ${escape(row.outcome)}</div>`
  )).join('');
  els.ending.innerHTML = banner + ending + '<h3>The days you flew</h3>' + log;
  playVoice();
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

let voiceToken = 0;
function playVoice() {
  if (!els.voice.checked) return;
  const token = ++voiceToken;
  call('/api/speak').then((data) => {
    if (token !== voiceToken || !data.audio) return;
    const player = new Audio(data.audio);
    player.play().catch(() => {});
  }).catch(() => {});
}

function startFlight() {
  mode = 'fly';
  landing = false;
  nextDay.hidden = true;
  els.scene.classList.remove('busy');
  els.scene.innerHTML = '<p class="narration">Catch the fish. Dodge branches and crows. The nest repairs you, the boat feeds you, and the river is a low dangerous meal.</p>';
  flight = {
    t0: performance.now(),
    y: 170,
    vy: 0,
    objects: [],
    spawnIn: 500,
    fish: 0,
    hits: 0,
    nest: false,
    boat: false,
    river: 0,
    riverAt: 0,
    nestSpawned: false,
    boatSpawned: false,
    flash: '',
  };
  sky.focus();
  armSounds();
}

async function finishFlight() {
  if (landing || !flight) return;
  landing = true;
  mode = 'story';
  const flown = flight;
  flight = null;
  els.scene.classList.add('busy');
  els.scene.innerHTML = '<p class="narration">You land in the branches...</p>';
  try {
    showStory(await call('/api/land', {
      fish: flown.fish,
      hits: flown.hits,
      nest: flown.nest,
      boat: flown.boat,
      river: flown.river,
    }));
  } catch (err) {
    els.scene.classList.remove('busy');
    els.scene.innerHTML = `<p class="narration">${escape(err.message)}</p>`;
    nextDay.hidden = false;
  }
}

async function begin() {
  mode = 'wait';
  flight = null;
  els.ending.hidden = true;
  sky.hidden = false;
  els.fly.hidden = false;
  nextDay.hidden = true;
  els.scene.classList.add('busy');
  els.scene.innerHTML = '<p class="narration">The sun rises over the nest...</p>';
  try {
    renderHud(await call('/api/start'));
    startFlight();
  } catch (err) {
    els.scene.classList.remove('busy');
    els.scene.innerHTML = `<p class="narration">${escape(err.message)}</p>`;
  }
}

function spawn(kind, width, height) {
  const y = kind === 'boat' ? height * 0.84
    : kind === 'nest' ? height * 0.32
    : kind === 'fish' ? height * (0.8 + Math.random() * 0.05)
    : height * (0.14 + Math.random() * 0.42);
  const radius = kind === 'gust' ? 46 : kind === 'boat' || kind === 'nest' ? 36 : 18;
  flight.objects.push({ kind, x: width + 50, y, r: radius, got: false });
}

function paint(now) {
  resize();
  const { width, height } = view;
  const period = world.period || 'day';
  const top = period === 'dawn' ? '#f6d7a8' : period === 'day' ? '#8ecae6' : period === 'dusk' ? '#f4a261' : '#1d2a4a';
  const bottom = period === 'dawn' ? '#e7a16a' : period === 'day' ? '#d8f3dc' : period === 'dusk' ? '#5c4d7a' : '#121a16';
  const skyFill = ctx.createLinearGradient(0, 0, 0, height);
  skyFill.addColorStop(0, top);
  skyFill.addColorStop(1, bottom);
  ctx.fillStyle = skyFill;
  ctx.fillRect(0, 0, width, height);

  if (mode === 'fly' && flight) {
    const dt = Math.min(0.05, (now - (flight.last || now)) / 1000);
    flight.last = now;
    const elapsed = now - flight.t0;
    let speed = 220;
    if (keys.has('ArrowLeft') || keys.has('KeyA')) speed = 120;
    if (keys.has('ArrowRight') || keys.has('KeyD')) speed = 320;
    if (keys.has('ArrowUp') || keys.has('KeyW')) flight.vy -= 520 * dt;
    if (keys.has('ArrowDown') || keys.has('KeyS')) flight.vy += 520 * dt;
    if (pointer.on) flight.vy += (pointer.y - flight.y) * 2.2 * dt;
    flight.vy *= 0.92;
    flight.y = Math.max(28, Math.min(height - 24, flight.y + flight.vy * dt));
    flight.scroll = (flight.scroll || 0) + speed * dt;

    if (elapsed > 6500 && !flight.nestSpawned) {
      spawn('nest', width, height);
      flight.nestSpawned = true;
    }
    if (elapsed > 13500 && !flight.boatSpawned) {
      spawn('boat', width, height);
      flight.boatSpawned = true;
    }
    flight.spawnIn -= dt * 1000;
    if (flight.spawnIn <= 0) {
      const roll = Math.random();
      const kind = roll > 0.9 ? 'gust' : roll > 0.74 ? 'crow' : roll > 0.5 ? 'branch' : 'fish';
      spawn(kind, width, height);
      flight.spawnIn = 680;
    }

    const eagleX = width * 0.24;
    for (const obj of flight.objects) {
      obj.x -= speed * dt;
      if (obj.got) continue;
      if (Math.hypot(eagleX - obj.x, flight.y - obj.y) > obj.r + 14) continue;
      obj.got = true;
      if (obj.kind === 'fish') {
        flight.fish += 1;
        flight.flash = 'fish';
      } else if (obj.kind === 'branch' || obj.kind === 'crow') {
        flight.hits += 1;
        flight.flash = 'hit';
      } else if (obj.kind === 'nest') {
        flight.nest = true;
        flight.flash = 'nest';
      } else if (obj.kind === 'boat') {
        flight.boat = true;
        flight.flash = 'boat';
      } else if (obj.kind === 'gust') {
        flight.vy += obj.y < flight.y ? 160 : -160;
        flight.flash = 'gust';
      }
    }
    flight.objects = flight.objects.filter((obj) => obj.x > -80);
    if (flight.y > height * 0.84 && now - flight.riverAt > 900) {
      flight.river += 1;
      flight.riverAt = now;
      flight.vy = -80;
      flight.flash = 'river';
    }
    drawWorld(now, eagleX, flight.y, flight.objects, flight);
    drawHud(Math.max(0, FLIGHT_MS - elapsed) / 1000, flight);
    if (elapsed >= FLIGHT_MS) finishFlight();
  } else {
    drawWorld(now, width * 0.24, height * 0.42, [], null);
    ctx.fillStyle = 'rgba(36,27,46,0.78)';
    ctx.fillRect(16, 16, 220, 32);
    ctx.fillStyle = '#fdf3e2';
    ctx.font = '600 15px Manrope, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(mode === 'story' ? 'Landed. Read the day.' : 'Ready to fly.', 28, 38);
  }
  requestAnimationFrame(paint);
}

function drawWorld(now, eagleX, eagleY, objects, live) {
  const { width, height } = view;
  const riverY = height * 0.78;
  const shift = live ? (live.scroll || 0) : now / 20;
  ctx.fillStyle = '#4f6b3a';
  ctx.beginPath();
  ctx.moveTo(0, height * 0.7);
  ctx.quadraticCurveTo(width * 0.5, height * 0.6, width, height * 0.68);
  ctx.lineTo(width, height);
  ctx.lineTo(0, height);
  ctx.fill();
  ctx.fillStyle = '#3d8ea3';
  ctx.fillRect(0, riverY, width, height - riverY);
  ctx.strokeStyle = 'rgba(253,243,226,0.45)';
  ctx.lineWidth = 2;
  for (let i = 0; i < 4; i++) {
    const y = riverY + 16 + i * 18;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.quadraticCurveTo(width * 0.5, y + Math.sin(shift / 40 + i) * 4, width, y);
    ctx.stroke();
  }
  if (world.raining) {
    ctx.strokeStyle = 'rgba(216,243,220,0.4)';
    for (let i = 0; i < 16; i++) {
      const x = (i * 70 + now / 8) % width;
      ctx.beginPath();
      ctx.moveTo(x, (i * 36) % height);
      ctx.lineTo(x - 8, (i * 36) % height + 16);
      ctx.stroke();
    }
  }
  for (const obj of objects) drawObject(obj);
  drawEagle(eagleX, eagleY, now);
}

function drawObject(obj) {
  ctx.save();
  ctx.translate(obj.x, obj.y);
  ctx.globalAlpha = obj.got ? 0.35 : 1;
  if (obj.kind === 'fish') {
    ctx.fillStyle = '#ffcf7a';
    ctx.beginPath();
    ctx.ellipse(0, 0, 16, 7, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(-14, 0);
    ctx.lineTo(-24, -6);
    ctx.lineTo(-24, 6);
    ctx.fill();
  } else if (obj.kind === 'branch') {
    ctx.strokeStyle = '#6b4632';
    ctx.lineWidth = 6;
    ctx.beginPath();
    ctx.moveTo(-20, 8);
    ctx.lineTo(18, -10);
    ctx.stroke();
  } else if (obj.kind === 'crow') {
    ctx.fillStyle = '#241b2e';
    ctx.beginPath();
    ctx.ellipse(0, 0, 14, 6, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(-4, 0);
    ctx.lineTo(-18, -12);
    ctx.lineTo(2, -2);
    ctx.fill();
  } else if (obj.kind === 'gust') {
    ctx.strokeStyle = 'rgba(253,243,226,0.8)';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.arc(0, 0, 28, 0.4, 2.2);
    ctx.stroke();
  } else if (obj.kind === 'nest') {
    ctx.fillStyle = '#7c9c4a';
    ctx.beginPath();
    ctx.arc(0, 0, 28, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#c4a574';
    ctx.fillRect(-16, 6, 32, 8);
    label('NEST');
  } else if (obj.kind === 'boat') {
    ctx.fillStyle = '#f6a25c';
    ctx.beginPath();
    ctx.moveTo(-26, 0);
    ctx.lineTo(26, 0);
    ctx.lineTo(16, 12);
    ctx.lineTo(-16, 12);
    ctx.fill();
    label('BOAT');
  }
  ctx.restore();
}

function label(text) {
  ctx.fillStyle = '#fdf3e2';
  ctx.font = '700 12px Manrope, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(text, 0, -34);
}

function drawEagle(x, y, now) {
  const flap = Math.sin(now / 90) * 10;
  ctx.save();
  ctx.translate(x, y);
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
}

function drawHud(seconds, live) {
  const labelText = `${seconds.toFixed(0)}s   fish ${live.fish}   hits ${live.hits}`;
  ctx.font = '700 16px Manrope, sans-serif';
  ctx.fillStyle = 'rgba(36,27,46,0.78)';
  ctx.fillRect(16, 16, ctx.measureText(labelText).width + 28, 34);
  ctx.fillStyle = '#fdf3e2';
  ctx.textAlign = 'left';
  ctx.fillText(labelText, 28, 39);
  const ratio = seconds / 20;
  ctx.fillStyle = 'rgba(36,27,46,0.35)';
  ctx.fillRect(16, view.height - 18, view.width - 32, 8);
  ctx.fillStyle = '#f6a25c';
  ctx.fillRect(16, view.height - 18, (view.width - 32) * ratio, 8);
}

sky.addEventListener('pointerdown', (event) => {
  const rect = sky.getBoundingClientRect();
  pointer.y = event.clientY - rect.top;
  pointer.on = true;
  sky.focus();
  armSounds();
});
sky.addEventListener('pointermove', (event) => {
  if (!pointer.on) return;
  pointer.y = event.clientY - sky.getBoundingClientRect().top;
});
window.addEventListener('pointerup', () => { pointer.on = false; });
window.addEventListener('keydown', (event) => {
  const fly = ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'KeyA', 'KeyD', 'KeyW', 'KeyS'];
  if (fly.includes(event.code)) {
    event.preventDefault();
    keys.add(event.code);
    armSounds();
  }
});
window.addEventListener('keyup', (event) => keys.delete(event.code));
nextDay.addEventListener('click', startFlight);
els.restart.addEventListener('click', begin);

const bag = { ctx: null, nodes: null };
function chirp() {
  if (!bag.ctx || bag.ctx.state !== 'running' || !els.sounds.checked) return;
  const time = bag.ctx.currentTime;
  const osc = bag.ctx.createOscillator();
  const gain = bag.ctx.createGain();
  osc.type = 'sine';
  osc.frequency.setValueAtTime(1900 + Math.random() * 400, time);
  osc.frequency.exponentialRampToValueAtTime(2800 + Math.random() * 500, time + 0.09);
  gain.gain.setValueAtTime(0.0001, time);
  gain.gain.exponentialRampToValueAtTime(0.04, time + 0.02);
  gain.gain.exponentialRampToValueAtTime(0.0001, time + 0.16);
  osc.connect(gain).connect(bag.ctx.destination);
  osc.start(time);
  osc.stop(time + 0.18);
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
