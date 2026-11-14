from core.story import FALLBACK_SCENES
from core.voice import speak, speak_scene

for sc in FALLBACK_SCENES:
    speak_scene(sc)
    print('cached:', sc['narration'][:30])
speak('Your chicks fledge and soar over the river. The nest is safe.')
speak('The nest could not hold on this time. Try again, and choose differently.')
