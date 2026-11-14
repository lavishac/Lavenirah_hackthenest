import json
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

# Ann Arbor: the Huron River runs along the university campus.
LATITUDE = 42.2808
LONGITUDE = -83.7430
ZONE = ZoneInfo('America/Detroit')
PLACE = 'Ann Arbor'
RIVER = 'Huron River'

_CODES = {
    0: 'Clear',
    1: 'Mainly clear',
    2: 'Partly cloudy',
    3: 'Overcast',
    45: 'Fog',
    48: 'Fog',
    51: 'Drizzle',
    53: 'Drizzle',
    55: 'Drizzle',
    61: 'Rain',
    63: 'Rain',
    65: 'Heavy rain',
    71: 'Snow',
    73: 'Snow',
    75: 'Heavy snow',
    80: 'Rain showers',
    81: 'Rain showers',
    82: 'Heavy showers',
    95: 'Thunderstorm',
}


def clock_for(when):
    hour = when.hour % 12 or 12
    suffix = 'AM' if when.hour < 12 else 'PM'
    return f'{hour}:{when.minute:02d} {suffix}'


def period_for(hour):
    if 5 <= hour < 8:
        return 'dawn'
    if 8 <= hour < 17:
        return 'day'
    if 17 <= hour < 20:
        return 'dusk'
    return 'night'


def _fallback():
    now = datetime.now(ZONE)
    return {
        'place': PLACE,
        'river': RIVER,
        'clock': clock_for(now),
        'hour': now.hour,
        'period': period_for(now.hour),
        'temp_f': None,
        'wind_mph': 8,
        'summary': 'Weather unavailable',
        'raining': False,
        'live': False,
    }


def michigan_now():
    """Current Ann Arbor time and weather. Time is America/Detroit; weather is Open-Meteo."""
    url = (
        'https://api.open-meteo.com/v1/forecast'
        f'?latitude={LATITUDE}&longitude={LONGITUDE}'
        '&current=temperature_2m,weather_code,wind_speed_10m'
        '&temperature_unit=fahrenheit&wind_speed_unit=mph'
        '&timezone=America%2FDetroit'
    )
    try:
        with urllib.request.urlopen(url, timeout=8) as resp:
            current = json.loads(resp.read().decode())['current']
        when = datetime.fromisoformat(current['time']).replace(tzinfo=ZONE)
        code = int(current['weather_code'])
        return {
            'place': PLACE,
            'river': RIVER,
            'clock': clock_for(when),
            'hour': when.hour,
            'period': period_for(when.hour),
            'temp_f': round(current['temperature_2m']),
            'wind_mph': round(current['wind_speed_10m']),
            'summary': _CODES.get(code, 'Mixed skies'),
            'raining': code in {51, 53, 55, 61, 63, 65, 80, 81, 82, 95},
            'live': True,
        }
    except (OSError, KeyError, ValueError, json.JSONDecodeError):
        return _fallback()
