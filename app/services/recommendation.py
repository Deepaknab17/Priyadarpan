import random
from app.models import Song
RECOMMENDATION_COUNT = 3
def emotional_progression(mood):
    base_valence = mood.valence
    base_energy = mood.energy
    # Step 1 — emotional match
    match_songs = list(
        Song.objects.filter(
            valence__gte=base_valence - 0.2,
            valence__lte=base_valence + 0.1,
            energy__gte=base_energy - 0.2,
            energy__lte=base_energy + 0.2,
            is_available=True
        )
    )
    # Step 2 — slight uplift
    uplift_songs = list(
        Song.objects.filter(
            valence__gt=base_valence + 0.1,
            valence__lte=base_valence + 0.4,
            energy__gte=base_energy,
            is_available=True
        )
    )
    # Step 3 — stronger uplift
    surprise_songs = list(
        Song.objects.filter(
            valence__gte=base_valence + 0.4,
            energy__gte=base_energy,
            is_available=True
        )
    )
    selected_songs = []
    if match_songs:
        selected_songs.append(random.choice(match_songs))
    if uplift_songs:
        selected_songs.append(random.choice(uplift_songs))
    if surprise_songs:
        selected_songs.append(random.choice(surprise_songs))
    # fallback if we don't have enough songs
    if len(selected_songs) < RECOMMENDATION_COUNT:
        remaining = list(Song.objects.filter(is_available=True).exclude(id__in=[song.id for song in selected_songs]))
        while len(selected_songs) < RECOMMENDATION_COUNT and remaining:
            song = random.choice(remaining)
            selected_songs.append(song)
            remaining.remove(song)
    return selected_songs