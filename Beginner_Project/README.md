# 🪺 Nest Defender

Nest Defender is a voice-narrated adventure where an AI storyteller writes the scenes and plain code keeps the game fair.

You play a parent eagle defending a nest beside a river near campus. Each day Gemini writes a short scene with three choices (safe, risky, clever), ElevenLabs reads it aloud with a different voice per character, and your choices change **nest health** and **food**. Survive 8 days and the chicks fledge.

## How it works

```
Python rules   decide what happens (health, food, dice)      <- testable, reliable
Gemini         writes the story and the three choices         <- creative
ElevenLabs     speaks it, one voice per character             <- the wow factor
Streamlit      bars, buttons, audio player                    <- the page
```

Under the hood:
- **Probabilistic outcome resolution** in plain Python (`core/game.py`). The AI never decides who wins.
- **JSON validation with a safe fallback** (`core/story.py`). If Gemini's reply is broken, a hand-written scene is used instead, so the game never crashes.
- **Cached text-to-speech** (`core/voice.py`). Each line is generated once and saved to disk.

## Run it

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then paste your keys into .env
python -m pytest -q         # 8 passed
streamlit run app.py
```

Turn both toggles off in the sidebar to play without any API keys.

## Project layout

| File | What it does |
|------|--------------|
| `core/game.py` | Game rules: health, food, dice |
| `core/story.py` | Gemini prompt, JSON parsing, backup scenes |
| `core/voice.py` | ElevenLabs voices with a disk cache |
| `app.py` | Streamlit page |
| `tests/test_game.py` | Tests for rules and parsing |
| `scripts/prewarm.py` | Pre-generates audio for the backup scenes |
