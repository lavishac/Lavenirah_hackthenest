import html

import streamlit as st
from dotenv import load_dotenv

from core.game import MAX_TURNS, State, resolve
from core.story import ending_text, next_scene
from core.voice import speak, speak_scene

load_dotenv()
st.set_page_config(page_title='Nest Defender', page_icon='🪺', layout='wide')
ss = st.session_state

KIND_LABEL = {
    'cautious': 'Safe',
    'bold': 'Risky',
    'clever': 'Clever',
}

st.markdown(
    """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Source+Sans+3:wght@400;600;700&display=swap');

  html, body, [class*="css"] {
    font-family: "Source Sans 3", "Segoe UI", sans-serif;
  }
  .stApp {
    background:
      radial-gradient(1200px 500px at 10% -10%, rgba(228, 177, 90, 0.16), transparent 55%),
      radial-gradient(900px 420px at 100% 0%, rgba(79, 158, 176, 0.14), transparent 50%),
      #14211c;
  }
  .block-container {
    max-width: 1040px;
    padding-top: 1.4rem;
    padding-bottom: 3rem;
  }
  header[data-testid="stHeader"] { background: transparent; }
  [data-testid="stSidebar"] {
    background: #18261f;
    border-right: 1px solid rgba(246, 241, 230, 0.08);
  }
  h1, h2, h3, .story-title, .scene-kicker {
    font-family: Fraunces, Georgia, serif;
  }
  .story-title {
    font-size: 3.1rem;
    line-height: 0.95;
    margin: 0;
    color: #f6f1e6;
    letter-spacing: -0.03em;
  }
  .story-sub {
    margin: 0.35rem 0 0;
    color: #d9cbb4;
    font-size: 1.05rem;
  }
  .stage {
    margin: 1rem 0 1.1rem;
    border-radius: 22px;
    overflow: hidden;
    border: 1px solid rgba(246, 241, 230, 0.12);
    box-shadow: 0 18px 50px rgba(0, 0, 0, 0.28);
    background: #0f1915;
  }
  .stage svg { display: block; width: 100%; height: auto; }
  .day-row {
    display: flex;
    gap: 0.45rem;
    align-items: center;
    margin: 0.2rem 0 0.9rem;
  }
  .day-pip {
    width: 1.7rem;
    height: 0.45rem;
    border-radius: 99px;
    background: rgba(246, 241, 230, 0.16);
  }
  .day-pip.on { background: #e4b15a; }
  .day-pip.now { background: #f3e2bc; box-shadow: 0 0 0 3px rgba(228, 177, 90, 0.25); }
  .day-label { margin-left: auto; color: #d9cbb4; font-weight: 600; }
  .meters { display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; margin-bottom: 1rem; }
  .meter {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(246, 241, 230, 0.1);
    border-radius: 16px;
    padding: 0.75rem 0.9rem 0.85rem;
  }
  .meter-label {
    display: flex;
    justify-content: space-between;
    color: #f6f1e6;
    font-weight: 700;
    margin-bottom: 0.4rem;
  }
  .meter-track {
    height: 0.7rem;
    border-radius: 99px;
    background: rgba(0, 0, 0, 0.28);
    overflow: hidden;
  }
  .meter-fill { height: 100%; border-radius: 99px; }
  .meter-fill.health { background: linear-gradient(90deg, #c4524a, #e7b15a); }
  .meter-fill.food { background: linear-gradient(90deg, #2f7f86, #8fd0c4); }
  .scene-card {
    background: rgba(246, 241, 230, 0.05);
    border: 1px solid rgba(246, 241, 230, 0.1);
    border-radius: 20px;
    padding: 1.15rem 1.25rem 0.4rem;
    margin-bottom: 0.4rem;
  }
  .scene-kicker {
    color: #e4b15a;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    font-size: 0.78rem;
    margin-bottom: 0.45rem;
  }
  .narration {
    font-family: Fraunces, Georgia, serif;
    font-size: 1.45rem;
    line-height: 1.35;
    color: #f8f3ea;
    margin: 0 0 0.8rem;
  }
  .dialogue {
    display: flex;
    gap: 0.75rem;
    align-items: flex-start;
    background: rgba(15, 25, 21, 0.55);
    border-radius: 14px;
    padding: 0.75rem 0.85rem;
    margin-bottom: 0.8rem;
  }
  .who {
    font-weight: 700;
    color: #e4b15a;
    min-width: 5.5rem;
  }
  .line { color: #f6f1e6; }
  .choice-kicker {
    display: inline-block;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    border-radius: 99px;
    padding: 0.18rem 0.55rem;
    margin-bottom: 0.35rem;
  }
  .tag-cautious { color: #d7f5df; background: rgba(92, 168, 112, 0.22); }
  .tag-bold { color: #ffd7cf; background: rgba(196, 82, 74, 0.28); }
  .tag-clever { color: #ffe7bf; background: rgba(228, 177, 90, 0.22); }
  div[data-testid="stColumn"] button {
    width: 100%;
    min-height: 5.2rem;
    white-space: normal;
    border-radius: 16px;
    border: 1px solid rgba(246, 241, 230, 0.16);
    background: #24382e;
    color: #f6f1e6;
    font-weight: 650;
    line-height: 1.3;
    padding: 0.8rem 0.85rem;
  }
  div[data-testid="stColumn"]:has(.tag-cautious) button { border-color: rgba(143, 208, 160, 0.7); }
  div[data-testid="stColumn"]:has(.tag-bold) button { border-color: rgba(224, 122, 110, 0.8); }
  div[data-testid="stColumn"]:has(.tag-clever) button { border-color: rgba(228, 177, 90, 0.8); }
  div[data-testid="stColumn"] button:hover { background: #2d4a3b; border-color: #f3e2bc; }
  .ending-banner {
    border-radius: 18px;
    padding: 1rem 1.15rem;
    margin: 0.4rem 0 0.8rem;
  }
  .ending-banner.won { background: rgba(92, 168, 112, 0.16); border: 1px solid rgba(143, 208, 160, 0.4); }
  .ending-banner.lost { background: rgba(196, 82, 74, 0.14); border: 1px solid rgba(224, 122, 110, 0.4); }
  .ending-banner h2 { margin: 0 0 0.25rem; color: #f6f1e6; }
  .score { font-size: 2rem; font-family: Fraunces, Georgia, serif; color: #e4b15a; margin: 0; }
  .log-item {
    padding: 0.55rem 0;
    border-bottom: 1px solid rgba(246, 241, 230, 0.1);
    color: #f6f1e6;
  }
  .sidebar-note { color: #d9cbb4; font-size: 0.95rem; line-height: 1.45; }
  @media (max-width: 800px) {
    .story-title { font-size: 2.3rem; }
    .meters { grid-template-columns: 1fr; }
    .narration { font-size: 1.2rem; }
  }
</style>
""",
    unsafe_allow_html=True,
)


def sky_colors(turn):
    if turn <= 2:
        return ('#f6d7a8', '#e7a16a')
    if turn <= 5:
        return ('#8ecae6', '#d8f3dc')
    if turn <= 7:
        return ('#f4a261', '#5c4d7a')
    return ('#1d2a4a', '#121a16')


def landscape(turn, health, food, mode='play'):
    top, bottom = sky_colors(8 if mode == 'lost' else turn)
    sun = '#f7e7b4' if turn <= 7 and mode != 'lost' else '#e7eefc'
    sun_y = 78 if turn <= 5 else 118
    storm = health <= 3 or mode == 'lost'
    fish = max(0, min(5, food // 2))
    chicks_in_nest = mode != 'won'
    title = 'The nest holds' if mode == 'won' else 'The river at dusk' if mode == 'lost' else 'The nest beside the river'
    fish_marks = ''.join(
        f'<ellipse cx="{250 + i * 28}" cy="{248 - (i % 2) * 8}" rx="10" ry="4" fill="#d8f3dc" opacity="0.85"/>'
        for i in range(fish)
    )
    chicks = (
        '<ellipse cx="612" cy="214" rx="8" ry="6" fill="#f4d58d"/>'
        '<ellipse cx="630" cy="214" rx="8" ry="6" fill="#f4d58d"/>'
        if chicks_in_nest
        else '<path d="M250 90 q18 -16 36 0 q-8 6 -18 4 q-10 2 -18 -4z" fill="#3e342c"/>'
        '<path d="M300 70 q18 -16 36 0 q-8 6 -18 4 q-10 2 -18 -4z" fill="#2c2824"/>'
    )
    rain = (
        '<g stroke="#d8f3dc" stroke-width="2" opacity="0.35">'
        '<path d="M40 20 l-18 46 M120 10 l-18 46 M200 30 l-18 46 M760 16 l-18 46 M840 36 l-18 46"/>'
        '</g>'
        if storm
        else ''
    )
    return f'''
<div class="stage">
<svg viewBox="0 0 960 320" role="img" aria-label="{html.escape(title)}">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{top}"/>
      <stop offset="100%" stop-color="{bottom}"/>
    </linearGradient>
  </defs>
  <rect width="960" height="320" fill="url(#sky)"/>
  {rain}
  <circle cx="780" cy="{sun_y}" r="34" fill="{sun}"/>
  <ellipse cx="180" cy="86" rx="54" ry="18" fill="#fff" opacity="0.35"/>
  <ellipse cx="230" cy="80" rx="36" ry="14" fill="#fff" opacity="0.28"/>
  <path d="M0 210 C 160 170, 280 230, 460 200 C 640 170, 760 230, 960 190 L 960 320 L 0 320 Z" fill="#214e3a"/>
  <path d="M0 250 C 180 230, 320 270, 520 246 C 700 226, 820 260, 960 240 L 960 320 L 0 320 Z" fill="#3d8ea3"/>
  {fish_marks}
  <rect x="860" y="150" width="46" height="62" fill="#243044" opacity="0.8"/>
  <polygon points="852,150 883,126 914,150" fill="#c4524a" opacity="0.85"/>
  <rect x="548" y="168" width="22" height="92" fill="#6b4632"/>
  <ellipse cx="560" cy="150" rx="78" ry="58" fill="#1f6b45"/>
  <ellipse cx="620" cy="168" rx="48" ry="36" fill="#2f7f4f"/>
  <ellipse cx="612" cy="228" rx="46" ry="16" fill="#c4a574"/>
  <path d="M572 226 Q612 198 654 226" fill="none" stroke="#8c6239" stroke-width="6"/>
  {chicks}
  <path d="M500 196 q34 -8 48 16 q-20 8 -34 2 q-6 10 -20 6 q2 -14 6 -24z" fill="#3e342c"/>
  <circle cx="542" cy="200" r="7" fill="#f4d58d"/>
</svg>
</div>
'''


def day_pips(turn, over):
    marks = []
    for n in range(1, MAX_TURNS + 1):
        klass = 'day-pip'
        if over or n < turn:
            klass += ' on'
        elif n == turn:
            klass += ' now'
        marks.append(f'<div class="{klass}"></div>')
    label = 'Fledged' if over and turn > MAX_TURNS else f'Day {min(turn, MAX_TURNS)} of {MAX_TURNS}'
    return f'<div class="day-row">{"".join(marks)}<div class="day-label">{label}</div></div>'


def meters(health, food):
    return f'''
<div class="meters">
  <div class="meter">
    <div class="meter-label"><span>Nest health</span><span>{health}/10</span></div>
    <div class="meter-track"><div class="meter-fill health" style="width:{health * 10}%"></div></div>
  </div>
  <div class="meter">
    <div class="meter-label"><span>Food</span><span>{food}/10</span></div>
    <div class="meter-track"><div class="meter-fill food" style="width:{food * 10}%"></div></div>
  </div>
</div>
'''


def show_scene(scene):
    dia = scene.get('dialogue') or {}
    speaker = html.escape(str(dia.get('speaker') or '').title())
    line = html.escape(str(dia.get('line') or ''))
    narration = html.escape(scene['narration'])
    dialogue = ''
    if speaker and line:
        dialogue = f'<div class="dialogue"><div class="who">{speaker}</div><div class="line">{line}</div></div>'
    st.markdown(
        f'<div class="scene-card"><div class="scene-kicker">Today by the river</div>'
        f'<p class="narration">{narration}</p>{dialogue}</div>',
        unsafe_allow_html=True,
    )


with st.sidebar:
    st.header('The nest')
    st.markdown(
        '<p class="sidebar-note">Safe repairs the nest. Clever brings food. '
        'Risky can pay off or leave the nest worse. The chicks eat every day, '
        'and danger can still strike.</p>',
        unsafe_allow_html=True,
    )
    ss.use_ai = st.toggle('Gemini game master', value=True)
    ss.use_voice = st.toggle('ElevenLabs voices', value=True)
    if st.button('Start a new story', use_container_width=True):
        for key in ('game', 'scene', 'audio', 'outcome', 'ending'):
            ss.pop(key, None)
        st.rerun()


def audio_for(scene):
    return speak_scene(scene) if ss.use_voice else None


def start():
    ss.game = State()
    ss.outcome = ''
    ss.ending = None
    ss.scene = next_scene(ss.game, '', ss.use_ai)
    ss.audio = audio_for(ss.scene)


if 'game' not in ss:
    with st.spinner('The sun rises over the nest...'):
        start()

g = ss.game
st.markdown(
    '<p class="story-title">Nest Defender</p>'
    '<p class="story-sub">Eight days. One nest. Keep the chicks fed and the branches holding.</p>',
    unsafe_allow_html=True,
)

if not g.over:
    st.markdown(landscape(g.turn, g.health, g.food), unsafe_allow_html=True)
    st.markdown(day_pips(g.turn, False), unsafe_allow_html=True)
    st.markdown(meters(g.health, g.food), unsafe_allow_html=True)
    if ss.outcome:
        st.info(ss.outcome)
    show_scene(ss.scene)
    if ss.audio:
        st.audio(ss.audio, format='audio/mp3', autoplay=True)
    cols = st.columns(3)
    for col, choice in zip(cols, ss.scene['choices']):
        kind = choice['kind']
        label = KIND_LABEL.get(kind, kind.title())
        with col:
            st.markdown(
                f'<div class="choice-kicker tag-{html.escape(kind)}">{html.escape(label)}</div>',
                unsafe_allow_html=True,
            )
            if st.button(choice['text'], key='c' + str(g.turn) + '_' + kind, use_container_width=True):
                ss.outcome = resolve(g, kind, choice['text'])
                with st.spinner('Meanwhile, in the trees...'):
                    if g.over:
                        ss.ending = ending_text(g, ss.use_ai)
                        ss.audio = speak(ss.ending) if ss.use_voice else None
                    else:
                        ss.scene = next_scene(g, ss.outcome, ss.use_ai)
                        ss.audio = audio_for(ss.scene)
                st.rerun()
else:
    mode = 'won' if g.won else 'lost'
    st.markdown(landscape(g.turn, g.health, g.food, mode), unsafe_allow_html=True)
    st.markdown(day_pips(g.turn, True), unsafe_allow_html=True)
    st.markdown(meters(g.health, g.food), unsafe_allow_html=True)
    if g.won:
        score = g.health * 10 + g.food * 5
        banner = (
            '<div class="ending-banner won"><h2>The chicks fledged.</h2>'
            f'<p class="score">{score}</p><p>Nest health and food, still holding on day eight.</p></div>'
        )
    else:
        banner = (
            '<div class="ending-banner lost"><h2>The nest was lost.</h2>'
            '<p>The river is still there. The next story can end differently.</p></div>'
        )
    st.markdown(banner, unsafe_allow_html=True)
    if ss.outcome:
        st.info(ss.outcome)
    if ss.ending:
        st.markdown(f'<p class="narration">{html.escape(ss.ending)}</p>', unsafe_allow_html=True)
    if ss.audio:
        st.audio(ss.audio, format='audio/mp3', autoplay=True)
    st.subheader('The days you flew')
    for turn, choice, outcome in g.log:
        st.markdown(
            '<div class="log-item"><strong>Day ' + str(turn) + '.</strong> '
            + html.escape(choice) + ' — ' + html.escape(outcome) + '</div>',
            unsafe_allow_html=True,
        )
    if st.button('Play again', use_container_width=True):
        start()
        st.rerun()
