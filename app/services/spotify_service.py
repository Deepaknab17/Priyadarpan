import requests

SPOTIFY_API_BASE = "https://api.spotify.com/v1"


# -------------------------
# HELPERS
# -------------------------

def chunk_list(lst, size=100):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]

# -------------------------
# PLAYLIST TRACKS
# -------------------------
def get_playlist_tracks(access_token, playlist_id):
    """
    Fetch tracks from a Spotify playlist (handles pagination)
    """
    url = f"{SPOTIFY_API_BASE}/playlists/{playlist_id}/tracks"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {"limit": 100}
    tracks = []
    while url:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code != 200:
            print("Spotify error:", response.status_code, response.text)
            raise Exception("Spotify API error")
        data = response.json()
        for item in data.get("items", []):
            track = item.get("track")
            # skip invalid tracks
            if not track or not track.get("id"):
                continue
            tracks.append({
                "id": track["id"],
                "title": track["name"],
                "artists": [a["name"] for a in track.get("artists", [])],
                "duration": track.get("duration_ms", 0) // 1000
            })
        url = data.get("next")
        params = None  
    return tracks


# -------------------------
# AUDIO FEATURES
# -------------------------

def get_audio_features(access_token, track_ids):
    """
    Fetch valence and energy (handles chunking)
    """
    url = f"{SPOTIFY_API_BASE}/audio-features"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    features = {}
    for chunk in chunk_list(track_ids, 100):
        params = {
            "ids": ",".join(chunk)
        }
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code != 200:
            print("Spotify error:", response.status_code, response.text)
            raise Exception("Spotify API error")
        data = response.json()
        for item in data.get("audio_features", []):
            if not item:
                continue
            features[item["id"]] = {
                "valence": item.get("valence", 0),
                "energy": item.get("energy", 0)
            }
    return features

# -------------------------
# SEARCH TRACKS
# -------------------------

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
    response = requests.get(url, headers=headers, params=params, timeout=10)

    if response.status_code != 200:
        print("Spotify error:", response.status_code, response.text)
        raise Exception("Spotify API error")
    data = response.json()
    tracks = []
    for item in data.get("tracks", {}).get("items", []):
        if not item or not item.get("id"):
            continue
        tracks.append({
            "id": item["id"],
            "title": item["name"],
            "artists": [a["name"] for a in item.get("artists", [])],
            "duration": item.get("duration_ms", 0) // 1000
        })
    return tracks