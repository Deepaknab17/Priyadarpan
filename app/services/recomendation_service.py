from app.models import MoodSession, SessionRecommendation,UserSongInteraction
from app.services.recommendation import emotional_progression

# ssession_recomendation
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

#  Fetch user interactions
    interactions = UserSongInteraction.objects.filter(
    user=user,
    tenant=tenant,
    mood=mood
)

    interaction_map = {
    i.song_id: i for i in interactions
}

#  scoring function
    def score(song):
        interaction = interaction_map.get(song.id)

        if not interaction:
            return 0

        score = 0
        score += interaction.play_count * 2
        score += interaction.liked * 5
        score -= interaction.skipped_count * 3

        return score

#  Apply ranking ON TOP of emotional progression
    songs = sorted(songs, key=lambda s: score(s) + (10 - songs.index(s)), reverse=True)

    recommendations = []
    for rank, song in enumerate(songs, start=1):
        rec = SessionRecommendation.objects.create(
            session=session,
            song=song,
            rank=rank
        )
        recommendations.append(rec)
    return session, recommendations