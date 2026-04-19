from app.models import MoodSession, SessionRecommendation,UserSongInteraction
from app.services.recommendation import emotional_progression

# ssession_recomendation
def generate_session_recommendations(user, mood):

    profile = getattr(user, "profile", None)
    if not profile or not profile.tenant:
        raise ValueError("User has no tenant")

    tenant = profile.tenant

    session = MoodSession.objects.create(
        tenant=tenant,
        user=user,
        mood=mood
    )

    songs = emotional_progression(mood, tenant)
    if not songs:
        return session, []

    interactions = UserSongInteraction.objects.filter(
        user=user,
        tenant=tenant,
        mood=mood
    )

    interaction_map = {i.song_id: i for i in interactions}

    def score(song):
        interaction = interaction_map.get(song.id)
        if not interaction:
            return 0

        s = 0
        s += interaction.play_count * 2
        s -= interaction.skipped_count * 3

        if interaction.liked:
            s += 5

        return s

    indexed_songs = list(enumerate(songs))

    ranked = sorted(
        indexed_songs,
        key=lambda pair: score(pair[1]) + (10 - pair[0]),
        reverse=True
    )

    songs = [s for _, s in ranked]

    recs = [
        SessionRecommendation(
            session=session,
            song=song,
            rank=rank
        )
        for rank, song in enumerate(songs, start=1)
    ]

    SessionRecommendation.objects.bulk_create(recs)

    return session, recs