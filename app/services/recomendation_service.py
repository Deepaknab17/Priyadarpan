from app.models import MoodSession, SessionRecommendation
from app.services.recommendation import emotional_progression


def generate_session_recomendations(user, mood):

    # create a new mood session
    session = MoodSession.objects.create(
        user=user,
        mood=mood
    )

    # get recommended songs from your algorithm
    songs = emotional_progression(mood)

    recomendations = []

    for rank, song in enumerate(songs, start=1):

        rec = SessionRecommendation.objects.create(
            session=session,
            song=song,
            rank=rank
        )

        recomendations.append(rec)

    return session, recomendations