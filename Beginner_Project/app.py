import streamlit as st
from dotenv import load_dotenv

from core.game import MAX_TURNS, State, resolve
from core.story import ending_text, next_scene
from core.voice import speak, speak_scene

load_dotenv()
st.set_page_config(page_title='Nest Defender', page_icon='🪺', layout='centered')
ss = st.session_state

with st.sidebar:
    st.header('Settings')
    ss.use_ai = st.toggle('Gemini game master', value=True)
    ss.use_voice = st.toggle('ElevenLabs voices', value=True)
    if st.button('🔄 New game'):
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
st.title('🪺 Nest Defender')
c1, c2 = st.columns(2)
c1.progress(g.health / 10, text='❤️ Nest health ' + str(g.health) + '/10')
c2.progress(g.food / 10, text='🐟 Food ' + str(g.food) + '/10')

if not g.over:
    st.caption('Day ' + str(g.turn) + ' of ' + str(MAX_TURNS))
    if ss.outcome:
        st.info(ss.outcome)
    scene = ss.scene
    st.markdown(scene['narration'])
    dia = scene.get('dialogue')
    if dia:
        st.markdown('> **' + dia['speaker'].title() + ':** ' + dia['line'])
    if ss.audio:
        st.audio(ss.audio, format='audio/mp3', autoplay=True)
    for i, ch in enumerate(scene['choices']):
        if st.button(ch['text'], key='c' + str(g.turn) + '_' + str(i)):
            ss.outcome = resolve(g, ch['kind'], ch['text'])
            with st.spinner('Meanwhile, in the trees...'):
                if g.over:
                    ss.ending = ending_text(g, ss.use_ai)
                    ss.audio = speak(ss.ending) if ss.use_voice else None
                else:
                    ss.scene = next_scene(g, ss.outcome, ss.use_ai)
                    ss.audio = audio_for(ss.scene)
            st.rerun()
else:
    if g.won:
        st.success('🎉 The chicks fledged! You defended the nest.')
        st.metric('Score', g.health * 10 + g.food * 5)
    else:
        st.error('💔 The nest was lost this time.')
    st.info(ss.outcome)
    if ss.ending:
        st.markdown(ss.ending)
    if ss.audio:
        st.audio(ss.audio, format='audio/mp3', autoplay=True)
    st.subheader('Your story')
    for turn, choice, outcome in g.log:
        st.write('**Day ' + str(turn) + ':** ' + choice + ' — ' + outcome)
    if st.button('Play again'):
        start()
        st.rerun()
