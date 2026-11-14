# Nest Defender

You play a parent eagle on the Huron River in Ann Arbor. Each day is a 20-second flight. Python decides the score, Gemini writes what that flight felt like, and a voice reads it after the words are already on the screen.

You start with nest health **6** and food **6**. There are **8** days. The chicks eat **1** food every day, even on a perfect flight. You win if both numbers are still above zero after day 8.

## How a flight works

During the flight, the browser is the game. Arrow keys or W A S D move the eagle. The page counts what you touch:

- A fish is **+1 food**.
- The boat is **+2 food**.
- The nest is **+2 health**.
- A branch or a crow is **−1 health**.
- Dipping into the river is **−1 health**.

When the timer ends, the browser sends those counts to Python. Python caps them so a made-up request cannot claim 100 fish, subtracts the chicks' meal, and stores the new health and food. Gemini never chooses those numbers. It only receives the sentence Python already wrote, such as "You brought home 4 fish. You struck 1 hazard. The chicks ate," and turns that into a short scene. If Gemini fails, that plain sentence is the scene.

The story appears right away. Then the page asks ElevenLabs to record it. If that account is out of credits, or no ElevenLabs key is set, the browser reads the same words for free. The river, wind, and bird sounds are also made in the browser. They do not use an API key.

The weather line is real. The server asks Open-Meteo for Ann Arbor, in Eastern time, and keeps that report for 10 minutes. Gemini is told the clock and the sky so the scene matches the time you are actually in.

```
Browser flight   arrow keys, fish, hazards, 20-second timer
Python rules     health, food, and the chicks' daily meal
Gemini           writes the story of the flight you just flew
Voice            ElevenLabs if it has credits, otherwise the browser
```

## Run it on your computer

From `Beginner_Project`:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # paste GEMINI_API_KEY into .env
python play.py
```

Open http://127.0.0.1:5050. Leave **Read the story aloud** checked. Turn **Gemini game master** off to play with the backup sentences and no API key.

## Deploy it

The live game is the Flask app, `Beginner_Project/play.py`. One Render web service keeps it online after the laptop is closed. `render.yaml` in this repo is the blueprint.

1. Push `main` to GitHub.
2. Open the blueprint: [Deploy Nest Defender on Render](https://render.com/deploy?repo=https://github.com/lavishac/Lavenirah_hackthenest).
3. Paste `GEMINI_API_KEY` when it asks. Leave `ELEVENLABS_API_KEY` blank unless that account has credits.
4. Share the `*.onrender.com` link. The next push to `main` redeploys it.

Game progress stays on that one server. Do not scale it to more than one instance.

## Project layout

| File | What it does |
|------|----------------|
| `Beginner_Project/play.py` | The server players use |
| `Beginner_Project/static/` | The flight page |
| `Beginner_Project/core/game.py` | Health, food, and the flight score |
| `Beginner_Project/core/story.py` | Gemini prompt and backup text |
| `Beginner_Project/core/voice.py` | ElevenLabs, with a disk cache |
| `Beginner_Project/core/michigan.py` | Ann Arbor time and weather |
| `Beginner_Project/app.py` | Earlier Streamlit page |
| `Beginner_Project/tests/test_game.py` | Tests for the rules |
