from app.models import Artist, Song
from app.services.spotify_service import (
    get_playlist_tracks,
    get_audio_features
)


def ingest_playlist(access_token, playlist_id):

    tracks = get_playlist_tracks(access_token, playlist_id)

    track_ids = [t["id"] for t in tracks]

    audio_features = get_audio_features(access_token, track_ids)

    for track in tracks:

        song, created = Song.objects.get_or_create(
            external_id=track["id"],
            defaults={
                "title": track["title"],
                "duration_seconds": track["duration"],
                "source": "spotify"
            }
        )

        if track["id"] in audio_features:

            features = audio_features[track["id"]]

            song.valence = features["valence"]
            song.energy = features["energy"]

            song.save(update_fields=["valence", "energy"])

        for artist_name in track["artists"]:

            artist, _ = Artist.objects.get_or_create(
                name=artist_name
            )

            song.artists.add(artist)