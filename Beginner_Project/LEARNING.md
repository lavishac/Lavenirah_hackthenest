# Learning Log: Nest Defender

**Pitch:** Nest Defender is a voice-narrated survival game where plain code keeps the game fair and an AI tells the story out loud.

**Demo path (3 min):** start a day → fly the 20-second river run (grab fish, dive on the boat for a big haul, patch the nest, dodge crows and branches, stay out of the river) → the day's scene appears on screen and a character reads it aloud in its own voice → play through to day 8; if health and food are both still above zero, the chicks fledge.

## What I did not know this morning
<!-- Each teammate writes ONE honest line. These are examples to react to, not to copy. -->
- Person 1:  _(e.g. "I'd never called an API from code I wrote myself.")_
- Person 2:  _(e.g. "I'd never used git with other people on the same repo.")_
- Person 3:  _(e.g. "I didn't know you could make a playable browser game without a game engine.")_

## Log
<!-- Every 2–3 hours: what we tried, what broke, what we learned. Add timestamps + screenshots. -->

### The decision we're proudest of: the AI narrates, it never decides
We split the game so Python owns every number and Gemini only describes them. The browser reports what the eagle touched during the flight; `core/game.py` (`resolve_flight`) **caps** those counts — fish and hits max out at 15, river at 8 — so a tampered request can't claim 100 fish. Then it subtracts the chicks' daily food and stores health and food. Gemini receives the sentence the code already wrote and turns it into a scene. Fair, testable, and impossible for the AI to break.

### Making Gemini reliable
- We ask Gemini for JSON (`response_mime_type`) so scenes come back clean instead of wrapped in ```json fences.
- Every reply is validated; if it's malformed or the API call fails, a hand-written fallback scene plays instead. A bad AI response can never crash the game.

### Making the voice the product (ElevenLabs)
- Each character has its own ElevenLabs voice (`core/voice.py`), and narration is cached on disk so repeated lines are instant and don't burn credits.
- If the ElevenLabs key is missing or out of credits, the browser's built-in voice reads the same words, so a demo never goes silent — but the real experience is the ElevenLabs cast.

### Difficulty tuning
- In the choice-based rules (`core/game.py resolve`), starting constants were HUNGER=1, THREAT_CHANCE=0.5, THREAT_DAMAGE=2.
- We simulated 20,000 games per strategy. A thoughtful player won 100% of the time — no tension. Raising THREAT_DAMAGE to 3 drops thoughtful play to ~85% and random play to ~26%, so losing is possible again. All 10 tests still pass.

### Real Michigan
- The weather line is real: Open-Meteo for Ann Arbor on the Huron River, in Eastern time, cached for 10 minutes (`core/michigan.py`).

### Tests and tooling
- 10 `pytest` checks on the scoring rules and the AI-reply parser; `ruff` for formatting and lint.

### Playtest notes
- _(Fill in: have 3 people outside the team play without instructions. Write exactly where they hesitated or got confused.)_

### Hardest bug
- _(Fill in the real one. A strong candidate from today: keeping the game playable when Gemini returns broken JSON — fixed with strict validation plus hand-written fallback scenes.)_
