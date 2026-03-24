MOOD_RESPONSES = {
    "happy": "That’s beautiful… let’s keep this feeling alive ✨",
    
    "sad": "It’s okay to feel this way… we don’t have to rush anything.",
    
    "broken": "Let’s wait here for a moment… I’m here with you. If you want, we can just sit and listen together.",
    
    "angry": "Take a breath… you don’t have to carry it all at once.",
    
    "calm": "Stay here… this moment doesn’t need to move."
}


def get_mood_response(mood):
    return MOOD_RESPONSES.get(
        mood.lower(),
        "Let’s just be here for a moment."
    )