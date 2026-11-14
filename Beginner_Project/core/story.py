import json
import os

from core.game import KINDS, MAX_TURNS

# New AI Studio accounts cannot call gemini-2.5-flash. Override with GEMINI_MODEL in .env.
MODEL = os.getenv('GEMINI_MODEL', 'gemini-3.1-flash-lite')
_client = None

FALLBACK_SCENES = [
    {
        'narration': 'Dawn over the river. Clouds roll in fast, and your two chicks chirp for breakfast.',
        'dialogue': {'speaker': 'mother', 'line': 'Quickly now, the storm will not wait for us!'},
        'choices': [
            {'text': 'Reinforce the nest with fresh branches', 'kind': 'cautious'},
            {'text': 'Dive into the river rapids for a big fish', 'kind': 'bold'},
            {'text': 'Follow the fishing boats, they stir up easy meals', 'kind': 'clever'},
        ],
    },
    {
        'narration': 'A crow lands on a nearby branch, eyeing the nest with a sly grin.',
        'dialogue': {'speaker': 'crow', 'line': 'Nice nest. Shame if something happened to it.'},
        'choices': [
            {'text': 'Spread your wings and guard the nest', 'kind': 'cautious'},
            {'text': 'Chase the crow across the treetops', 'kind': 'bold'},
            {'text': 'Offer the crow a deal: leftover scraps for peace', 'kind': 'clever'},
        ],
    },
    {
        'narration': 'Night falls. Wind howls through the tall trees and the nest sways.',
        'dialogue': None,
        'choices': [
            {'text': 'Huddle the chicks low in the nest', 'kind': 'cautious'},
            {'text': 'Fly out into the gusts to find shelter', 'kind': 'bold'},
            {'text': 'Wedge the nest tighter between two branches', 'kind': 'clever'},
        ],
    },
]


def fallback_scene(turn):
    return FALLBACK_SCENES[(turn - 1) % len(FALLBACK_SCENES)]


def valid_scene(d):
    """Is this scene safe to show? (Gemini sometimes returns broken JSON.)"""
    try:
        if not isinstance(d['narration'], str) or not d['narration'].strip():
            return False
        choices = d['choices']
        if len(choices) != 3 or {c['kind'] for c in choices} != set(KINDS):
            return False
        if not all(isinstance(c['text'], str) and c['text'].strip() for c in choices):
            return False
        dia = d.get('dialogue')
        if dia is not None and not (
            isinstance(dia.get('speaker'), str) and isinstance(dia.get('line'), str)
        ):
            return False
        return True
    except (KeyError, TypeError, AttributeError):
        return False


def parse_scene(text):
    """Turn the model's reply into a scene dict, or None if it is unusable."""
    if not text:
        return None
    start, end = text.find('{'), text.rfind('}')  # ignore ```json fences and chatter
    if start < 0 or end <= start:
        return None
    try:
        d = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return d if valid_scene(d) else None


def _ask_gemini(prompt, json_mode=False):
    global _client
    from google import genai

    _client = _client or genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    config = {'response_mime_type': 'application/json'} if json_mode else None
    return _client.models.generate_content(
        model=MODEL, contents=prompt, config=config
    ).text


EXAMPLE = {
    'narration': '2-3 sentences',
    'dialogue': {'speaker': 'crow', 'line': 'one short line'},
    'choices': [
        {'text': '...', 'kind': 'cautious'},
        {'text': '...', 'kind': 'bold'},
        {'text': '...', 'kind': 'clever'},
    ],
}


def build_prompt(state, last_outcome, setting=''):
    where = (setting + ' ') if setting else ''
    return (
        'You are the game master of a short, family-friendly, fictional adventure. The player is '
        'a parent eagle defending a nest in a tall tree beside the Huron River in Ann Arbor, '
        'Michigan. Dangers are scary but never graphic. ' + where +
        'Turn ' + str(state.turn) + ' of ' + str(MAX_TURNS) + '. Nest health ' + str(state.health) + '/10, '
        'food ' + str(state.food) + '/10. What just happened: ' + (last_outcome or 'the story begins') + '. '
        'Write the next scene. Reply with ONLY JSON shaped like this: ' + json.dumps(EXAMPLE) + ' '
        'Dialogue may be null. The speaker must be one of: crow, raccoon, mother, owl. '
        'Exactly three choices, one of each kind. Cautious means safe, bold means risky, '
        'clever means a smart trick. Keep each choice under 12 words. Do not mention numbers or game stats.'
    )


def next_scene(state, last_outcome, use_ai=True, setting=''):
    if use_ai:
        try:
            scene = parse_scene(_ask_gemini(build_prompt(state, last_outcome, setting), json_mode=True))
            if scene:
                return scene
        except Exception as err:
            print('Gemini failed:', err)
    return fallback_scene(state.turn)


def parse_flight(text):
    """A flight story is narration plus an optional spoken line, with no choices."""
    if not text:
        return None
    start, end = text.find('{'), text.rfind('}')
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(text[start : end + 1])
        narration = data['narration']
        if not isinstance(narration, str) or not narration.strip():
            return None
        dialogue = data.get('dialogue')
        if dialogue is not None and not (
            isinstance(dialogue.get('speaker'), str) and isinstance(dialogue.get('line'), str)
        ):
            return None
    except (KeyError, TypeError, AttributeError, json.JSONDecodeError):
        return None
    return {'narration': narration.strip(), 'dialogue': dialogue}


def flight_story(state, outcome, use_ai=True, setting=''):
    """Tell the day the player just flew. The numbers are already decided."""
    told = {
        'narration': outcome,
        'dialogue': {'speaker': 'mother', 'line': 'Hold the nest. Tomorrow we fly again.'},
    }
    if not use_ai:
        return told
    where = (setting + ' ') if setting else ''
    prompt = (
        'You are the game master of a short, family-friendly, fictional adventure. The player is '
        'a parent eagle who just flew beside the Huron River in Ann Arbor, Michigan. '
        + where +
        'Day just finished. Turn ' + str(state.turn) + ' of ' + str(MAX_TURNS) + ' is next. '
        'What the flight did: ' + outcome + ' '
        'Reply with ONLY JSON like {"narration":"2-3 sentences","dialogue":{"speaker":"mother","line":"one short line"}}. '
        'Dialogue may be null. The speaker must be one of: crow, raccoon, mother, owl. '
        'Describe the flight in the river world. Do not mention numbers, points, or game stats.'
    )
    try:
        told_by_model = parse_flight(_ask_gemini(prompt))
        if told_by_model:
            return told_by_model
    except Exception as err:
        print('Gemini failed:', err)
    return told


def ending_text(state, use_ai=True):
    base = (
        'Your chicks fledge and soar over the river. The nest is safe.'
        if state.won
        else 'The nest could not hold on this time. Try again, and choose differently.'
    )
    if not use_ai:
        return base
    prompt = (
        'Write a 2-sentence, family-friendly ending for a fictional eagle-nest adventure. '
        'Outcome: ' + ('the nest survived and the chicks fledged' if state.won else 'the nest was lost') + '. '
        'Keep it hopeful in tone. Reply with plain text only.'
    )
    try:
        return (_ask_gemini(prompt) or '').strip() or base
    except Exception as err:
        print('Gemini failed:', err)
        return base
