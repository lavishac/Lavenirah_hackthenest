# Nest Defender

*A voice-narrated survival game where plain code keeps the game fair and an AI tells the story out loud.*

## Inspiration
Most AI games let the model decide everything, so they feel random and can't be tested. We flipped it: the code decides what happens, and the AI only narrates it — out loud. We set it on the Huron River in Ann Arbor so the world (and the weather) is real.

## What it does
You're a parent eagle with eight days to get your chicks to fledge. Each day is a 20-second flight you fly in the browser with the arrow keys — grab fish and dive on the boat for food, touch the nest to repair it, dodge branches, crows and the river. When the timer ends, the game scores what you touched, feeds the hungry chicks, and updates nest health and food. Then **Gemini** turns that result into a short scene and **ElevenLabs** reads it aloud, each character in its own voice. Survive with both health and food above zero and the chicks fly.

## Why the voice is the product
This isn't text-to-speech on a README. Every scene is written to be *heard* — a sly crow, a worried mother, a steady narrator, each a distinct ElevenLabs voice — so you can look up from the screen and still be in the story. Our fallback (the browser's built-in voice) exists only so a dead API key never breaks a demo; the real experience is the ElevenLabs cast.

## How we built it
- **Python** owns the rules and the score, and caps the flight counts so a tampered request can't claim 100 fish. The AI never touches the numbers.
- **Gemini** receives the sentence Python already wrote and turns it into a scene. We ask it for JSON so the reply is clean; if it ever fails, the plain sentence is the scene.
- **ElevenLabs** narrates, with a per-character voice map and an on-disk audio cache so repeated lines are instant and cheap.
- **Flask** serves the live browser game; the flight canvas, river/wind/bird ambience, and the fallback voice all run in the browser with no API key.
- **Open-Meteo** gives the real Ann Arbor weather line, cached for 10 minutes.
- **pytest + ruff** keep the rules honest — 10 tests on the scoring and the AI-reply parser.

## Challenges we ran into
- Keeping the game fair: making the AI narrate without ever letting it decide the outcome.
- Making bad AI output impossible to crash on — we validate every reply and fall back to hand-written scenes.
- Tuning difficulty so a thoughtful player can still lose (we simulated 20,000 games to set the numbers).

## What we learned
Most of our team had never been to a hackathon. We learned to call the Gemini and ElevenLabs APIs from scratch, to design so the AI can't break the rules, and to test game logic. Our full before/after is in `LEARNING.md`.

## What's next
Saved stories per player (MongoDB + SSOJet sign-in), more characters and voices, and real Michigan events — a passing storm or a bright meteor — woven into the day.

## Tracks and prizes we're entering
- **Best Use of ElevenLabs** (primary — voice is the product)
- **MLH: Best Use of Gemini API** (Google Cloud project ID included)
- **Best Beginner**
- Overall prizes

## Built with
python, flask, google-gemini, elevenlabs, open-meteo, javascript, html5-canvas, pytest, ruff
