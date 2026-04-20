import random
from app.models import Song

RECOMMENDATION_COUNT = 3

VALENCE_RANGE = 0.2
UPLIFT_RANGE = 0.4


def pick_song(queryset, selected_ids):
    songs = list(queryset.exclude(id__in=selected_ids)[:10])
    if not songs:
        return None
    return random.choice(songs)


def emotional_progression(mood, tenant=None):

    base_valence = mood.valence or 0.5
    base_energy = mood.energy or 0.5

    selected_songs = []
    selected_ids = []

    # STEP 1 — Emotional match (stay in same mood)
    match_query = Song.objects.filter(
        tenant=tenant,
        valence__gte=base_valence - VALENCE_RANGE,
        valence__lte=base_valence + 0.1,
        energy__gte=base_energy - 0.2,
        energy__lte=base_energy + 0.2,
        is_available=True
    ).order_by("-play_count")

    song = pick_song(match_query, selected_ids)
    if song:
        selected_songs.append(song)
        selected_ids.append(song.id)

    # STEP 2 — Slight uplift (gentle improvement)
    uplift_query = Song.objects.filter(
        tenant=tenant,
        valence__gt=base_valence + 0.1,
        valence__lte=base_valence + UPLIFT_RANGE,
        energy__gte=base_energy,
        is_available=True
    ).order_by("-play_count")

    song = pick_song(uplift_query, selected_ids)
    if song:
        selected_songs.append(song)
        selected_ids.append(song.id)

    # STEP 3 — Strong uplift (positive push)
    surprise_query = Song.objects.filter(
        tenant=tenant,
        valence__gte=base_valence + UPLIFT_RANGE,
        energy__gte=base_energy,
        is_available=True
    ).order_by("-play_count")

    song = pick_song(surprise_query, selected_ids)
    if song:
        selected_songs.append(song)
        selected_ids.append(song.id)

    # FALLBACK — random fill
    if len(selected_songs) < RECOMMENDATION_COUNT:

        remaining = list(
            Song.objects.filter(
                tenant=tenant,
                is_available=True
            ).exclude(id__in=selected_ids)
        )

        while len(selected_songs) < RECOMMENDATION_COUNT and remaining:
            song = random.choice(remaining)
            selected_songs.append(song)
            remaining.remove(song)

    return selected_songs