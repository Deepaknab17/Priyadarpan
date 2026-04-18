import requests

SPOTIFY_API_BASE = "https://api.spotify.com/v1"


def get_playlist_tracks(access_token, playlist_id):
    """
    Fetch tracks from a Spotify playlist
    
    """

    url = f"{SPOTIFY_API_BASE}/playlists/{playlist_id}/tracks"
    print("URL:", url)

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    params = {
        "limit": 100
    }

    tracks = []

    while url:

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print("STATUS:", response.status_code)
            print("BODY:", response.text)
            raise Exception("Spotify API error")

        data = response.json()

        for item in data["items"]:

            track = item["track"]

            if not track:
                continue

            tracks.append({
                "id": track["id"],
                "title": track["name"],
                "artists": [a["name"] for a in track["artists"]],
                "duration": track["duration_ms"] // 1000
            })

        url = data["next"]
        params = None

    return tracks


def get_audio_features(access_token, track_ids):
    """
    Fetch valence and energy for multiple tracks
    """

    url = f"{SPOTIFY_API_BASE}/audio-features"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    params = {
        "ids": ",".join(track_ids)
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        raise Exception("Spotify API error")

    data = response.json()

    features = {}

    for item in data["audio_features"]:
        if not item:
            continue

        features[item["id"]] = {
            "valence": item["valence"],
            "energy": item["energy"]
        }

    return features
def search_tracks(access_token, query, limit=20):

    url = f"{SPOTIFY_API_BASE}/search"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    params = {
        "q": query,
        "type": "track",
        "limit": limit
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        raise Exception(f"Spotify API error: {response.status_code} - {response.text}")

    data = response.json()

    tracks = []

    for item in data["tracks"]["items"]:

        tracks.append({
            "id": item["id"],
            "title": item["name"],
            "artists": [a["name"] for a in item["artists"]],
            "duration": item["duration_ms"] // 1000
        })

    return tracks