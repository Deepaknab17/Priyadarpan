import random

MOOD_RESPONSES = {
    "happy": [
        "That’s beautiful… let’s keep this feeling alive",
        "Hold onto this moment… it’s yours.",
    ],
    "sad": [
        "It’s okay to feel this way… we don’t have to rush anything.",
        "You don’t have to fix it right now… just feel it.",
    ],
    "broken": [
        "Let’s wait here for a moment… I’m here with you.",
    ],
    "angry": [
        "Take a breath… you don’t have to carry it all at once.",
    ],
    "calm": [
        "Stay here… this moment doesn’t need to move.",
    ]
}


def get_mood_response(mood):
    mood = (mood or "").lower()

    responses = MOOD_RESPONSES.get(mood)

    if responses:
        return random.choice(responses)

    return "Let’s just be here for a moment."