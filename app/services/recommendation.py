import random
from app.models import Song


RECOMMENDATION_COUNT = 3


def emotional_progression(mood):

    base_value = mood.emotional_value

    # Step 1 — emotional match
    match_songs = list(
        Song.objects.filter(
            emotional_value__gte=base_value - 0.2,
            emotional_value__lte=base_value + 0.1,
            is_available=True
        )
    )

    # Step 2 — slight uplift
    uplift_songs = list(
        Song.objects.filter(
            emotional_value__gt=base_value + 0.1,
            emotional_value__lte=base_value + 0.4,
            is_available=True
        )
    )

    # Step 3 — stronger uplift / surprise
    surprise_songs = list(
        Song.objects.filter(
            emotional_value__gte=base_value + 0.4,
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

    if len(selected_songs) < RECOMMENDATION_COUNT:

        remaining = list(
            Song.objects.filter(is_available=True)
            .exclude(id__in=[song.id for song in selected_songs])
        )

        while len(selected_songs) < RECOMMENDATION_COUNT and remaining:

            song = random.choice(remaining)

            selected_songs.append(song)

            remaining.remove(song)

    return selected_songs