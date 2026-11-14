import json
import random

from core.game import MAX_TURNS, State, resolve
from core.story import fallback_scene, parse_scene, valid_scene


class NeverThreat(random.Random):
    """Always returns a high number: no danger happens and bold choices fail."""

    def random(self):
        return 0.99


class AlwaysLucky(random.Random):
    """Always returns a low number: bold choices work, but the danger also fires."""

    def random(self):
        return 0.0


def test_cautious_heals_and_eats():
    s = State()
    resolve(s, 'cautious', rng=NeverThreat())
    assert s.health == 8 and s.food == 5 and s.turn == 2


def test_clever_adds_food():
    s = State()
    resolve(s, 'clever', rng=NeverThreat())
    assert s.food == 7 and s.health == 6


def test_stats_are_clamped():
    s = State(health=10, food=10)
    resolve(s, 'cautious', rng=NeverThreat())
    assert s.health == 10


def test_bold_can_win_or_fail():
    ok, bad = State(), State()
    resolve(ok, 'bold', rng=AlwaysLucky())  # success, but danger also fires
    resolve(bad, 'bold', rng=NeverThreat())  # fails, no danger
    assert ok.food == 8 and bad.health == 4


def test_game_over_and_win():
    assert State(health=0).over and not State(health=0).won
    assert State(turn=MAX_TURNS + 1).won


def test_unknown_kind_raises():
    try:
        resolve(State(), 'sneaky')
    except ValueError:
        return
    raise AssertionError('should have raised')


def test_parse_scene_handles_fences_and_junk():
    scene = {
        'narration': 'A crow lands.',
        'dialogue': None,
        'choices': [
            {'text': 'Guard', 'kind': 'cautious'},
            {'text': 'Chase', 'kind': 'bold'},
            {'text': 'Bargain', 'kind': 'clever'},
        ],
    }
    good = 'Here you go: ```json ' + json.dumps(scene) + ' ```'
    assert parse_scene(good)['narration'] == 'A crow lands.'
    assert parse_scene('not json at all') is None
    assert parse_scene(json.dumps({'narration': 'x', 'choices': []})) is None


def test_fallback_scenes_are_valid():
    assert all(valid_scene(fallback_scene(t)) for t in range(1, 10))
