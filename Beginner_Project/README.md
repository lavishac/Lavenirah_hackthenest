# Nest Defender

**A voice-narrated survival game. Every day on the river is read aloud, each character in its own voice — the game is meant to be heard.**

You play a parent eagle on the Huron River in Ann Arbor. Each day is a 20-second flight. Python decides the score, Gemini writes what that flight felt like, and a voice reads it after the words are already on the screen.

You start with nest health **6** and food **6**. There are **8** days. The chicks eat **1** food every day, even on a perfect flight. You win if both numbers are still above zero after day 8.

## Tracks and prizes

One project, aimed where its core already lives — the voice.

- **Best Use of ElevenLabs (primary).** The game is meant to be *heard*: every day's scene is narrated aloud, each character in its own ElevenLabs voice. The voice is the product, not a feature bolted on.
- **MLH — Best Use of Gemini API.** Gemini is the storyteller that turns each flight's result into a scene. (Our Google Cloud project ID is in the Devpost submission.)
- **Best Beginner.** Most of our team is at their first hackathon — see `LEARNING.md` for the before/after and our hardest bug.
- **Overall prizes.** Judged science-fair style across all projects.

Optional if time allows: **MongoDB** (save each run) and **SSOJet** (sign-in for saved stories).

## How a flight works

During the flight, the browser is the game. Arrow keys or W A S D move the eagle. The page counts what you touch:

- A fish is **+1 food**.
- The boat is **+2 food**.
- The nest is **+2 health**.
- A branch or a crow is **−1 health**.
- Dipping into the river is **−1 health**.

When the timer ends, the browser sends those counts to Python. Python caps them so a made-up request cannot claim 100 fish, subtracts the chicks' meal, and stores the new health and food. Gemini never chooses those numbers. It only receives the sentence Python already wrote and turns that into a short scene. If Gemini fails, that plain sentence is the scene.

The story appears right away. Then the page asks ElevenLabs to record it. If that account is out of credits, or no ElevenLabs key is set, the browser reads the same words for free. The river, wind, and bird sounds are made in the browser and do not use an API key.

The weather line is real. The server asks Open-Meteo for Ann Arbor, in Eastern time, and keeps that report for 10 minutes.

## Run it

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # paste GEMINI_API_KEY into .env
python -m pytest -q
python play.py
```

Open http://127.0.0.1:5050.

## Deploy

Use the `render.yaml` blueprint at the root of the repo. Paste `GEMINI_API_KEY` in Render's settings. Leave `ELEVENLABS_API_KEY` blank unless that account has credits. The browser voice covers the narration. Keep the service at one instance, because the game state lives in memory on that machine.

| File | What it does |
|------|----------------|
| `play.py` | The server players use |
| `static/` | The flight page |
| `core/game.py` | Health, food, and the flight score |
| `core/story.py` | Gemini prompt and backup text |
| `core/voice.py` | ElevenLabs, with a disk cache |
| `core/michigan.py` | Ann Arbor time and weather |
| `app.py` | Earlier Streamlit page |
| `tests/test_game.py` | Tests for the rules |
