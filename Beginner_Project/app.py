import html
import time

import streamlit as st
from dotenv import load_dotenv

from ambience import campus_sounds
from core.game import MAX_TURNS, State, resolve
from core.michigan import michigan_now
from core.story import ending_text, next_scene
from core.voice import speak, speak_scene
from flight import flight_canvas

load_dotenv()
st.set_page_config(page_title='Nest Defender', page_icon='🪺', layout='wide')
ss = st.session_state

KIND_LABEL = {
    'cautious': 'Safe',
    'bold': 'Risky',
    'clever': 'Clever',
}
KIND_EFFECT = {
    'cautious': 'Fixes the nest',
    'clever': 'Finds food',
    'bold': 'A gamble: big meal or damage',
}

st.markdown(
    """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700&family=Space+Grotesk:wght@500;700&display=swap');

  html, body, [class*="css"] {
    font-family: Manrope, "Segoe UI", sans-serif;
  }
  .stApp {
    background:
      radial-gradient(900px 420px at 85% -10%, rgba(246, 162, 92, 0.28), transparent 55%),
      linear-gradient(180deg, #2b2140 0%, #411735 55%, #230e1c 100%);
  }
  .block-container {
    max-width: 1040px;
    padding-top: 1.4rem;
    padding-bottom: 3rem;
  }
  header[data-testid="stHeader"] { background: transparent; }
  [data-testid="stSidebar"] {
    background: #241b2e;
    border-right: 1px solid rgba(253, 243, 226, 0.12);
  }
  [data-testid="stSidebar"] button {
    background: #f6a25c;
    color: #241b2e;
    border: none;
    border-radius: 999px;
    font-weight: 700;
  }
  h1, h2, h3, .story-title, .scene-kicker {
    font-family: "Space Grotesk", Manrope, sans-serif;
  }
  .story-title {
    font-size: 3.1rem;
    line-height: 0.95;
    margin: 0;
    color: #fdf3e2;
    letter-spacing: -0.03em;
  }
  .story-sub {
    margin: 0.35rem 0 0;
    color: #ffe2c6;
    font-size: 1.05rem;
  }
  .stage {
    margin: 1rem 0 1.1rem;
    border-radius: 22px;
    overflow: hidden;
    border: 1px solid rgba(253, 243, 226, 0.16);
    box-shadow: 0 18px 50px rgba(19, 9, 17, 0.35);
    background: #130911;
  }
  .stage svg { display: block; width: 100%; height: auto; }
  .stage a { cursor: pointer; }
  .stage a:hover .hit { stroke: #f6f1e6; fill: rgba(246, 241, 230, 0.16); }
  .stage text { font-family: "Source Sans 3", sans-serif; font-weight: 700; letter-spacing: 0.08em; }
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
    background: rgba(253, 243, 226, 0.18);
  }
  .day-pip.on { background: #f6a25c; }
  .day-pip.now { background: #ffe9b0; box-shadow: 0 0 0 3px rgba(246, 162, 92, 0.35); }
  .day-label { margin-left: auto; color: #ffe2c6; font-weight: 600; }
  .meters { display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; margin-bottom: 1rem; }
  .meter {
    background: #fdf3e2;
    border: 1px solid #ffe9b0;
    border-radius: 16px;
    padding: 0.75rem 0.9rem 0.85rem;
  }
  .meter-label {
    display: flex;
    justify-content: space-between;
    color: #241b2e;
    font-weight: 700;
    margin-bottom: 0.4rem;
  }
  .meter-track {
    height: 0.7rem;
    border-radius: 99px;
    background: rgba(36, 27, 46, 0.12);
    overflow: hidden;
  }
  .meter-fill { height: 100%; border-radius: 99px; }
  .meter-fill.health { background: linear-gradient(90deg, #8b393c, #f6a25c); }
  .meter-fill.food { background: linear-gradient(90deg, #4f6b3a, #7c9c4a); }
  .scene-card {
    background: #fdf3e2;
    border: 1px solid #ffe9b0;
    border-radius: 20px;
    padding: 1.15rem 1.25rem 0.4rem;
    margin-bottom: 0.4rem;
  }
  .scene-kicker {
    color: #e47646;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    font-size: 0.78rem;
    margin-bottom: 0.45rem;
  }
  .narration {
    font-family: "Space Grotesk", Manrope, sans-serif;
    font-size: 1.45rem;
    line-height: 1.35;
    color: #241b2e;
    margin: 0 0 0.8rem;
  }
  .dialogue {
    display: flex;
    gap: 0.75rem;
    align-items: flex-start;
    background: #2b2140;
    border-radius: 14px;
    padding: 0.75rem 0.85rem;
    margin-bottom: 0.8rem;
  }
  .who {
    font-weight: 700;
    color: #ffcf7a;
    min-width: 5.5rem;
  }
  .line { color: #fdf3e2; }
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
  .tag-cautious { color: #241b2e; background: #7c9c4a; }
  .tag-bold { color: #fdf3e2; background: #8b393c; }
  .tag-clever { color: #241b2e; background: #ffcf7a; }
  div[data-testid="stColumn"] button {
    width: 100%;
    min-height: 5.2rem;
    white-space: normal;
    border-radius: 16px;
    border: 1px solid rgba(253, 243, 226, 0.2);
    background: #3a2a52;
    color: #fdf3e2;
    font-weight: 650;
    line-height: 1.3;
    padding: 0.8rem 0.85rem;
  }
  div[data-testid="stColumn"]:has(.tag-cautious) button { border-color: #7c9c4a; }
  div[data-testid="stColumn"]:has(.tag-bold) button { border-color: #e47646; }
  div[data-testid="stColumn"]:has(.tag-clever) button { border-color: #ffcf7a; }
  div[data-testid="stColumn"] button:hover { background: #f6a25c; color: #241b2e; border-color: #ffe9b0; }
  div[data-testid="stHorizontalBlock"]:has(.hot-spot) {
    margin-top: -4.6rem;
    margin-bottom: 0.4rem;
    position: relative;
    z-index: 3;
  }
  div[data-testid="stHorizontalBlock"]:has(.hot-spot) button {
    min-height: 3.1rem;
    background: rgba(20, 33, 28, 0.72);
    border-style: dashed;
    letter-spacing: 0.06em;
  }
  .ending-banner {
    border-radius: 18px;
    padding: 1rem 1.15rem;
    margin: 0.4rem 0 0.8rem;
  }
  .ending-banner.won { background: rgba(124, 156, 74, 0.2); border: 1px solid #7c9c4a; }
  .ending-banner.lost { background: rgba(139, 57, 60, 0.28); border: 1px solid #e47646; }
  .ending-banner h2 { margin: 0 0 0.25rem; color: #fdf3e2; }
  .score { font-size: 2rem; font-family: "Space Grotesk", Manrope, sans-serif; color: #ffcf7a; margin: 0; }
  .log-item {
    padding: 0.55rem 0;
    border-bottom: 1px solid rgba(253, 243, 226, 0.12);
    color: #fdf3e2;
  }
  .sidebar-note { color: #ffe2c6; font-size: 0.95rem; line-height: 1.45; }
  .sidebar-note p { margin: 0 0 0.75rem; }
  .sidebar-note strong { color: #fdf3e2; }
  .guide { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.7rem; margin: 0.2rem 0 0.8rem; }
  .guide div { border-radius: 14px; padding: 0.7rem 0.8rem 0.8rem; background: #fdf3e2; border: 1px solid #ffe9b0; }
  .guide strong { display: block; margin-bottom: 0.15rem; }
  .guide span { color: #241b2e; font-size: 0.92rem; }
  .guide .safe strong { color: #3a5230; }
  .guide .clever strong { color: #8b393c; }
  .guide .risky strong { color: #e47646; }
  .warn { margin: 0 0 0.8rem; padding: 0.7rem 0.9rem; border-radius: 12px; background: rgba(246, 162, 92, 0.18); border: 1px solid #f6a25c; color: #fdf3e2; }
  @media (max-width: 800px) {
    .story-title { font-size: 2.3rem; }
    .meters { grid-template-columns: 1fr; }
    .narration { font-size: 1.2rem; }
    .guide { grid-template-columns: 1fr; }
  }
</style>
""",
    unsafe_allow_html=True,
)


def sky_colors(period):
    if period == 'dawn':
        return ('#f6d7a8', '#e7a16a')
    if period == 'day':
        return ('#8ecae6', '#d8f3dc')
    if period == 'dusk':
        return ('#f4a261', '#5c4d7a')
    return ('#1d2a4a', '#121a16')


def landscape(turn, health, food, mode='play', reaction=None, period='day', raining=False):
    top, bottom = sky_colors('night' if mode == 'lost' else period)
    sun = '#e7eefc' if period == 'night' or mode == 'lost' else '#f7e7b4'
    sun_y = 70 if period == 'day' else 120
    storm = health <= 3 or mode == 'lost' or reaction == 'bold' or raining
    fish = max(0, min(5, food // 2))
    if reaction == 'clever':
        fish = min(5, fish + 2)
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
    branches = (
        '<path d="M548 214 l34 -22 M578 220 l40 -16 M612 216 l30 -20" stroke="#6b4632" stroke-width="4" fill="none"/>'
        if reaction == 'cautious'
        else ''
    )
    splash = (
        '<circle class="splash" cx="210" cy="268" r="14" fill="none" stroke="#f6f1e6" stroke-width="2"/>'
        '<circle cx="210" cy="268" r="26" fill="none" stroke="#d8f3dc" stroke-width="2"/>'
        if reaction == 'bold'
        else ''
    )
    targets = ''
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
  {splash}
  <path d="M352 268 l28 -10 34 10 -10 8 h-42 z" fill="#c4a574"/>
  <path d="M378 258 v-18" stroke="#f6f1e6" stroke-width="2"/>
  <rect x="860" y="150" width="46" height="62" fill="#243044" opacity="0.8"/>
  <polygon points="852,150 883,126 914,150" fill="#c4524a" opacity="0.85"/>
  <rect x="548" y="168" width="22" height="92" fill="#6b4632"/>
  <ellipse cx="560" cy="150" rx="78" ry="58" fill="#1f6b45"/>
  <ellipse cx="620" cy="168" rx="48" ry="36" fill="#2f7f4f"/>
  <ellipse cx="612" cy="228" rx="46" ry="16" fill="#c4a574"/>
  <path d="M572 226 Q612 198 654 226" fill="none" stroke="#8c6239" stroke-width="6"/>
  {chicks}
  {branches}
  <path d="M500 196 q34 -8 48 16 q-20 8 -34 2 q-6 10 -20 6 q2 -14 6 -24z" fill="#3e342c"/>
  <circle cx="542" cy="200" r="7" fill="#f4d58d"/>
  {targets}
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


def reset_story():
    for key in ('game', 'scene', 'audio', 'outcome', 'ending', 'reaction', 'pending_kind'):
        ss.pop(key, None)


def queue_choice(kind):
    ss.pending_kind = kind


with st.sidebar:
    st.header('How to play')
    st.markdown(
        '<div class="sidebar-note">'
        '<p><strong>1. Read the day.</strong> The story tells you what is happening by the river.</p>'
        '<p><strong>2. Pick a place.</strong> Fly the eagle there and click, or press the button under the story.</p>'
        '<p><strong>Nest · safe.</strong> Fixes the branches.</p>'
        '<p><strong>Boat · clever.</strong> Finds food.</p>'
        '<p><strong>River · risky.</strong> A big meal, or a hard fall.</p>'
        '<p><strong>3. Last 8 days.</strong> Keep nest health and food above zero. The chicks eat every day.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    ss.use_ai = st.toggle('Gemini game master', value=True)
    ss.use_voice = st.toggle('ElevenLabs voices', value=True)
    ss.use_sounds = st.toggle('River, wind, and birds', value=True)
    if st.button('Start a new story', use_container_width=True, on_click=reset_story):
        pass


def audio_for(scene):
    return speak_scene(scene) if ss.use_voice else None


def start():
    ss.game = State()
    ss.outcome = ''
    ss.ending = None
    ss.reaction = None
    ss.scene = next_scene(ss.game, '', ss.use_ai, ss.setting)
    ss.audio = audio_for(ss.scene)


def play(kind):
    """Resolve the choice and load the next scene in this same run."""
    match = next(c for c in ss.scene['choices'] if c['kind'] == kind)
    ss.outcome = resolve(ss.game, kind, match['text'])
    ss.reaction = kind
    if ss.game.over:
        ss.ending = ending_text(ss.game, ss.use_ai)
        ss.audio = speak(ss.ending) if ss.use_voice else None
    else:
        ss.scene = next_scene(ss.game, ss.outcome, ss.use_ai, ss.setting)
        ss.audio = audio_for(ss.scene)


def campus():
    cached = ss.get('campus')
    if cached and time.time() - cached['_at'] < 600:
        return cached
    report = michigan_now()
    report['_at'] = time.time()
    ss.campus = report
    return report


here = campus()
temp = f'{here["temp_f"]}°F · ' if here['temp_f'] is not None else ''
ss.setting = (
    f'Right now in {here["place"]} it is {here["clock"]}, {here["summary"].lower()}, '
    f'{temp}wind {here["wind_mph"]} mph. Match this time of day and sky. '
    'Do not invent a different clock time.'
)

if 'game' not in ss:
    with st.spinner('The sun rises over the nest...'):
        start()

picked = st.query_params.get('choice')
queued = ss.pop('pending_kind', None)
choice = picked if picked in KIND_LABEL else queued
if choice and not ss.game.over:
    if picked:
        st.query_params.clear()
    with st.spinner('Meanwhile, in the trees...'):
        play(choice)

g = ss.game
st.markdown(
    '<p class="story-title">Nest Defender</p>'
    '<p class="story-sub">Keep the nest standing and the chicks fed for 8 days.</p>',
    unsafe_allow_html=True,
)
st.caption(
    f'{here["place"]}, on the {here["river"]} · {here["clock"]} · {temp}{here["summary"]} · '
    f'wind {here["wind_mph"]} mph'
)
if ss.use_sounds:
    campus_sounds(here['wind_mph'])

if not g.over:
    st.markdown(day_pips(g.turn, False), unsafe_allow_html=True)
    st.markdown(meters(g.health, g.food), unsafe_allow_html=True)
    if ss.outcome:
        st.info(ss.outcome)
    if g.health <= 3 or g.food <= 3:
        worry = []
        if g.health <= 3:
            worry.append('the branches are failing')
        if g.food <= 3:
            worry.append('the chicks are hungry')
        st.markdown(
            '<div class="warn">Watch the bars. Right now ' + ' and '.join(worry) + '.</div>',
            unsafe_allow_html=True,
        )
    show_scene(ss.scene)
    if ss.audio:
        st.audio(ss.audio, format='audio/mp3', autoplay=True)
    st.markdown(
        '<div class="guide">'
        '<div class="safe"><strong>Nest · safe</strong><span>Fixes the nest. The sure repair.</span></div>'
        '<div class="clever"><strong>Boat · clever</strong><span>Finds food for the chicks.</span></div>'
        '<div class="risky"><strong>River · risky</strong><span>A big meal, or a hard fall.</span></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown('**Fly there.** Move with the mouse or arrow keys, then click or press space.')
    landed = flight_canvas(
        g.turn, g.health, g.food, here['period'], here['raining'], here['wind_mph']
    )
    if landed:
        with st.spinner('Meanwhile, in the trees...'):
            play(landed)
        st.rerun()
    cols = st.columns(3)
    for col, choice in zip(cols, ss.scene['choices']):
        kind = choice['kind']
        label = KIND_LABEL.get(kind, kind.title())
        effect = KIND_EFFECT.get(kind, '')
        with col:
            st.markdown(
                f'<div class="choice-kicker tag-{html.escape(kind)}">{html.escape(label)} · {html.escape(effect)}</div>',
                unsafe_allow_html=True,
            )
            st.button(
                choice['text'],
                key='c' + str(g.turn) + '_' + kind,
                use_container_width=True,
                on_click=queue_choice,
                args=(kind,),
            )
else:
    mode = 'won' if g.won else 'lost'
    st.markdown(
        landscape(g.turn, g.health, g.food, mode, reaction=ss.reaction, period=here['period'], raining=here['raining']),
        unsafe_allow_html=True,
    )
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
    st.button('Play again', use_container_width=True, on_click=reset_story)
