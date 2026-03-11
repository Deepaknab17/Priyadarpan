from app.models import MoodSession, SessionRecommendation
from app.services.recommendation import emotional_progression


def generate_session_recomendations(user, mood):

    tenant = user.profile.tenant

    # create session with tenant
    session = MoodSession.objects.create(
        tenant=tenant,
        user=user,
        mood=mood
    )

    # generate songs
    songs = emotional_progression(mood, tenant)

    recommendations = []

    for rank, song in enumerate(songs, start=1):

        rec = SessionRecommendation.objects.create(
            session=session,
            song=song,
            rank=rank
        )

        recommendations.append(rec)

    return session, recommendations