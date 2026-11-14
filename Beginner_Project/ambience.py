import streamlit as st

_AMBIENCE = st.components.v2.component(
        'nest_ambience',
        isolate_styles=True,
        js=r"""
export default function(component) {
  const { data, parentElement } = component;
  const wind = Math.max(4, Math.min(20, (data && data.wind) || 8));
  const note = document.createElement("p");
  note.textContent = "Click anywhere to hear the river, the wind, and a bird.";
  note.style.margin = "0";
  note.style.color = "#d9cbb4";
  note.style.font = "600 14px sans-serif";
  parentElement.appendChild(note);

  const bag = window.__nestAmbience || (window.__nestAmbience = { ctx: null, nodes: null });

  function chirp() {
    if (!bag.ctx || bag.ctx.state !== "running") return;
    const now = bag.ctx.currentTime;
    const osc = bag.ctx.createOscillator();
    const gain = bag.ctx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(1900 + Math.random() * 400, now);
    osc.frequency.exponentialRampToValueAtTime(2800 + Math.random() * 500, now + 0.09);
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(0.04, now + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.16);
    osc.connect(gain).connect(bag.ctx.destination);
    osc.start(now);
    osc.stop(now + 0.18);
  }

  function start() {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    if (!bag.ctx) bag.ctx = new AudioCtx();
    if (bag.ctx.state === "suspended") bag.ctx.resume();
    if (bag.nodes) {
      bag.nodes.wind.gain.value = 0.03 + wind / 180;
      note.textContent = "You can hear the Huron River, the wind, and a bird.";
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
      river: layer("lowpass", 280, 0.16),
      wind: layer("bandpass", 700, 0.03 + wind / 180),
    };
    bag.bird = setInterval(chirp, 2800);
    chirp();
    note.textContent = "You can hear the Huron River, the wind, and a bird.";
  }

  function arm() { start(); }
  window.addEventListener("pointerdown", arm);
  window.addEventListener("keydown", arm);
  parentElement._stop = () => {
    window.removeEventListener("pointerdown", arm);
    window.removeEventListener("keydown", arm);
  };
}
""",
    )


def campus_sounds(wind_mph):
    _AMBIENCE(key='campus-sounds', data={'wind': wind_mph}, height=28)
