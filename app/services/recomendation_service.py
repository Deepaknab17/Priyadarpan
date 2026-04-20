from app.models import MoodSession, SessionRecommendation, UserSongInteraction
from app.services.recommendation import emotional_progression


def generate_session_recommendations(user, mood):

    if not mood:
        raise ValueError("Invalid mood")

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

    # Deduplicate
    seen = set()
    unique_songs = []
    for s in songs:
        if s.id not in seen:
            unique_songs.append(s)
            seen.add(s.id)
    songs = unique_songs

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

        if interaction.liked:
            s += 20

        s += interaction.play_count * 3
        s -= interaction.skipped_count * 5

        return s

    def rank_value(index, song):
        return score(song) + (10 - index)

    indexed_songs = list(enumerate(songs))

    ranked = sorted(
        indexed_songs,
        key=lambda pair: rank_value(pair[0], pair[1]),
        reverse=True
    )

    songs = [s for _, s in ranked][:10]

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