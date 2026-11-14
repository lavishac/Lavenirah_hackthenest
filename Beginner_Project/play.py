"""Live browser game. The picture stays in motion; only the story changes.

Run from this folder:
    python play.py
Then open http://127.0.0.1:5050
"""

import hashlib
import os
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory, session

load_dotenv()

from core.game import State, resolve
from core.michigan import michigan_now
from core.story import ending_text, next_scene
from core.voice import CACHE, speak, speak_scene

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET', 'nest-defender-local')
GAMES = {}
CAMPUS = {'at': 0, 'report': None, 'setting': ''}


def campus():
    if CAMPUS['report'] and time.time() - CAMPUS['at'] < 600:
        return CAMPUS['report'], CAMPUS['setting']
    here = michigan_now()
    temp = f'{here["temp_f"]}°F, ' if here['temp_f'] is not None else ''
    setting = (
        f'Right now in {here["place"]} it is {here["clock"]}, {here["summary"].lower()}, '
        f'{temp}wind {here["wind_mph"]} mph. Match this time of day and sky. '
        'Do not invent a different clock time.'
    )
    CAMPUS['at'] = time.time()
    CAMPUS['report'] = here
    CAMPUS['setting'] = setting
    return here, setting


def game():
    gid = session.get('gid')
    if gid and gid in GAMES:
        return GAMES[gid]
    gid = uuid.uuid4().hex
    session['gid'] = gid
    GAMES[gid] = {
        'state': State(),
        'scene': None,
        'outcome': '',
        'ending': None,
        'use_ai': True,
        'use_voice': True,
    }
    return GAMES[gid]


def clip_url(audio):
    if not audio:
        return None
    name = hashlib.sha1(audio).hexdigest() + '.mp3'
    path = Path(CACHE) / name
    if not path.exists():
        path.write_bytes(audio)
    return '/audio/' + name


def pack(g, here):
    state = g['state']
    return {
        'health': state.health,
        'food': state.food,
        'turn': state.turn,
        'over': state.over,
        'won': state.won,
        'score': state.health * 10 + state.food * 5,
        'outcome': g['outcome'],
        'ending': g['ending'],
        'scene': g['scene'],
        'log': [
            {'turn': turn, 'choice': choice, 'outcome': outcome}
            for turn, choice, outcome in state.log
        ],
        'campus': {
            'place': here['place'],
            'river': here['river'],
            'clock': here['clock'],
            'period': here['period'],
            'temp_f': here['temp_f'],
            'wind_mph': here['wind_mph'],
            'summary': here['summary'],
            'raining': here['raining'],
        },
    }


def fresh(g, use_ai, use_voice):
    here, setting = campus()
    g['use_ai'] = use_ai
    g['use_voice'] = use_voice
    g['state'] = State()
    g['outcome'] = ''
    g['ending'] = None
    g['scene'] = next_scene(g['state'], '', use_ai, setting)
    audio = speak_scene(g['scene']) if use_voice else None
    body = pack(g, here)
    body['audio'] = clip_url(audio)
    return body


@app.get('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.get('/audio/<name>')
def audio(name):
    if len(name) != 44 or not name.endswith('.mp3') or not name[:-4].isalnum():
        return ('', 404)
    return send_from_directory(CACHE, name)


@app.post('/api/start')
def start():
    body = request.get_json(silent=True) or {}
    g = game()
    return jsonify(fresh(
        g,
        bool(body.get('use_ai', True)),
        bool(body.get('use_voice', True)),
    ))


@app.post('/api/choose')
def choose():
    body = request.get_json(silent=True) or {}
    kind = body.get('kind')
    g = game()
    here, setting = campus()
    if g['scene'] is None or g['state'].over:
        return jsonify(pack(g, here))
    match = next((c for c in g['scene']['choices'] if c['kind'] == kind), None)
    if match is None:
        return jsonify({'error': 'Pick the nest, the boat, or the river.'}), 400
    g['use_ai'] = bool(body.get('use_ai', g['use_ai']))
    g['use_voice'] = bool(body.get('use_voice', g['use_voice']))
    g['outcome'] = resolve(g['state'], kind, match['text'])
    if g['state'].over:
        g['ending'] = ending_text(g['state'], g['use_ai'])
        g['scene'] = None
        audio = speak(g['ending']) if g['use_voice'] else None
    else:
        g['scene'] = next_scene(g['state'], g['outcome'], g['use_ai'], setting)
        audio = speak_scene(g['scene']) if g['use_voice'] else None
    packed = pack(g, here)
    packed['audio'] = clip_url(audio)
    return jsonify(packed)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5050, debug=False, threaded=True)
