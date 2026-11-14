import random
from dataclasses import dataclass, field

KINDS = ('cautious', 'bold', 'clever')
MAX_TURNS = 8
MAX_STAT = 10
HUNGER = 1  # food lost every turn (the chicks are hungry)
THREAT_CHANCE = 0.5  # chance of a danger each turn
THREAT_DAMAGE = 2


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
