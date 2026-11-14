import random
from dataclasses import dataclass, field

KINDS = ('cautious', 'bold', 'clever')
MAX_TURNS = 8
MAX_STAT = 10
HUNGER = 1  # food lost every turn (the chicks are hungry)
THREAT_CHANCE = 0.5  # chance of a danger each turn
THREAT_DAMAGE = 3


@dataclass
class State:
    health: int = 6
    food: int = 6
    turn: int = 1
    log: list = field(default_factory=list)  # (turn, choice text, outcome text)

    @property
    def over(self):
        return self.health <= 0 or self.food <= 0 or self.turn > MAX_TURNS

    @property
    def won(self):
        return self.health > 0 and self.food > 0 and self.turn > MAX_TURNS


def _clamp(v):
    return max(0, min(MAX_STAT, v))


def _count(value, limit):
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = 0
    return max(0, min(limit, number))


def resolve_flight(state, fish, hits, nest=False, boat=False, river=0):
    """Apply one flown day. The flight decides the numbers; this only keeps them fair."""
    fish = _count(fish, 15)
    hits = _count(hits, 15)
    river = _count(river, 8)
    dh = (2 if nest else 0) - hits - river
    df = fish + (2 if boat else 0) - HUNGER
    meal = '1 fish' if fish == 1 else f'{fish} fish'
    bits = [f'You brought home {meal}.']
    if boat:
        bits.append('The fishing boat stirred up an easy meal.')
    if nest:
        bits.append('You patched the nest on the way past.')
    if hits:
        struck = '1 hazard' if hits == 1 else f'{hits} hazards'
        bits.append(f'You struck {struck}.')
    if river:
        bits.append('The river clipped your wings.')
    bits.append('The chicks ate.')
    msg = ' '.join(bits)
    state.health = _clamp(state.health + dh)
    state.food = _clamp(state.food + df)
    state.log.append((state.turn, 'Flew the river', msg))
    state.turn += 1
    return msg


def resolve(state, kind, text='', rng=random):
    """Apply one choice plus the world's reaction. Returns a short outcome message."""
    if kind == 'cautious':
        dh, df, msg = 2, 0, 'You played it safe and repaired the nest.'
    elif kind == 'clever':
        dh, df, msg = 0, 2, 'A clever idea brought in extra food.'
    elif kind == 'bold':
        if rng.random() < 0.5:
            dh, df, msg = 1, 3, 'The bold move worked! A big haul and a boost.'
        else:
            dh, df, msg = -2, 0, 'The bold move backfired and the nest took damage.'
    else:
        raise ValueError('unknown kind: ' + str(kind))
    df -= HUNGER
    if rng.random() < THREAT_CHANCE:
        dh -= THREAT_DAMAGE
        msg += ' A danger struck the nest.'
    state.health = _clamp(state.health + dh)
    state.food = _clamp(state.food + df)
    state.log.append((state.turn, text or kind, msg))
    state.turn += 1
    return msg
