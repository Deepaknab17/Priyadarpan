
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets

from django.shortcuts import redirect, get_object_or_404, render
from django.utils import timezone
from django.contrib.auth import authenticate, login

import requests, urllib.parse
from datetime import timedelta
import logging

from django.conf import settings
from django.core.cache import cache

from .models import Memory, Mood, Song, MoodSession,UserSongInteraction, Profile, Tenant


from .serializers import MemorySerializer, MoodSerializer,SongSerializer, TenantSignupSerializer
# SERVICES
from app.services.recommendation import generate_session_recommendations
from app.services.spotify_service import search_tracks
from app.services.ingestion import ingest_playlist
from app.services.spotify_service  import activate_premium
from app.services.user_service import create_user_with_profile
from .services.mood_engine import get_mood_response


# create your views here

logger = logging.getLogger(__name__)


# -------------------------
# HELPERS
# -------------------------

def safe_user(req):
    if not req.user.is_authenticated:
        return None
    return req.user


def get_tenant(req):
    user = safe_user(req)
    if not user:
        return None
    return user.profile.tenant


def is_premium(profile):
    return profile and profile.premium_until and profile.premium_until > timezone.now()


def rate_limit(key, limit=10, window=60):
    current = cache.get(key, 0)
    if current >= limit:
        return False
    cache.set(key, current + 1, timeout=window)
    return True


# -------------------------
# LOGIN
# -------------------------

def login_view(req):
    if req.method == "POST":
        email = req.POST.get("email")
        password = req.POST.get("password")

        user = authenticate(req, username=email, password=password)

        if user:
            login(req, user)

            role = user.profile.role

            if role == "superadmin":
                return redirect("superadmin_dashboard")
            elif role == "admin":
                return redirect("admin_dashboard")
            else:
                return redirect("user_dashboard")

        return render(req, "login.html", {"error": "Invalid credentials"})

    return render(req, "login.html")


# -------------------------
# DASHBOARDS
# -------------------------

def superadmin_dashboard(req):
    if not safe_user(req) or req.user.profile.role != "superadmin":
        return redirect("login")
    return render(req, "superadmin.html")


def admin_dashboard(req):
    if not safe_user(req) or req.user.profile.role != "admin":
        return redirect("login")
    return render(req, "admin.html")


def user_dashboard(req):
    if not safe_user(req) or req.user.profile.role != "user":
        return redirect("login")
    return render(req, "user.html")


# -------------------------
# TENANT SIGNUP
# -------------------------

class TenantSignupView(APIView):

    def post(self, request):

        if not safe_user(request) or request.user.profile.role != "superadmin":
            return Response({"error": "Unauthorized"}, status=403)

        serializer = TenantSignupSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Tenant created"}, status=201)

        return Response(serializer.errors, status=400)


# -------------------------
# SPOTIFY
# -------------------------

def spotify_login(request):
    params = {
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "scope": "user-read-private user-read-email"
    }
    url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(params)
    return redirect(url)


def spotify_callback(request):
    code = request.GET.get("code")

    if not code:
        return Response({"error": "No code"}, status=400)

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
            "client_id": settings.SPOTIFY_CLIENT_ID,
            "client_secret": settings.SPOTIFY_CLIENT_SECRET,
        },
    )

    if response.status_code != 200:
        return Response({"error": "Spotify failed"}, status=400)

    data = response.json()

    request.session["access_token"] = data.get("access_token")
    request.session["refresh_token"] = data.get("refresh_token")

    return Response({"message": "Spotify connected"})


def ingest_spotify_playlist(req):

    if not safe_user(req) or req.user.profile.role != "superadmin":
        return Response({"error": "Unauthorized"}, status=403)

    key = f"rl:{req.user.id}:ingest"
    if not rate_limit(key):
        return Response({"error": "Too many requests"}, status=429)

    token = req.session.get("access_token")
    playlist_id = req.GET.get("playlist_id")

    if not token:
        return Response({"error": "Spotify not connected"}, status=400)

    if not playlist_id or len(playlist_id) > 200:
        return Response({"error": "Invalid playlist_id"}, status=400)

    try:
        ingest_playlist(token, playlist_id)
    except Exception:
        logger.error("Ingest failed", exc_info=True)
        return Response({"error": "Ingest failed"}, status=500)

    return Response({"message": "Playlist ingested"})

def test_spotify_tracks(request):

    token = request.session.get("access_token")

    if not token:
        return Response({"error": "Spotify not connected"}, status=400)

    try:
        tracks = search_tracks(token, "happy")
    except Exception:
        logger.error("Spotify test failed", exc_info=True)
        return Response({"error": "Spotify failed"}, status=500)

    return Response({
        "count": len(tracks),
        "tracks": tracks[:5]
    })


# -------------------------
# PREMIUM
# -------------------------

def check_premium(req):
    if safe_user(req):
        return Response({"premium": is_premium(req.user.profile)})
    return Response({"premium": False})


# -------------------------
# SONGS
# -------------------------

def list_songs(req):
    songs = Song.objects.filter(is_available=True).values(
        "id", "title", "external_id", "is_premium"
    )
    return Response(list(songs))


def play_song(req, song_id):
    song = get_object_or_404(Song, id=song_id)

    profile = req.user.profile if safe_user(req) else None

    if song.is_premium:
        if not profile:
            return Response({"error": "Premium required"}, status=403)

        if profile.role not in ["admin", "superadmin"] and not is_premium(profile):
            return Response({"error": "Premium required"}, status=403)

    return Response({"song": song.title})


# -------------------------
# MEMORY
# -------------------------

class MemoryViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, req):
        memories = Memory.objects.filter(user=req.user, tenant=get_tenant(req))
        return Response(MemorySerializer(memories, many=True).data)

    def create(self, req):
        serializer = MemorySerializer(data=req.data)

        if serializer.is_valid():
            serializer.save(user=req.user, tenant=get_tenant(req))
            return Response(serializer.data)

        return Response(serializer.errors, status=400)


# -------------------------
# MOOD SYSTEM
# -------------------------

class MoodViewSet(viewsets.ViewSet):

    def list(self, req):
        moods = Mood.objects.all()
        return Response(MoodSerializer(moods, many=True).data)

    def retrieve(self, req, pk=None):
        mood = get_object_or_404(Mood, pk=pk)
        return Response(MoodSerializer(mood).data)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def experience(self, req, pk=None):

        key = f"rl:{req.user.id}:experience"
        if not rate_limit(key):
            return Response({"error": "Too many requests"}, status=429)

        mood = get_object_or_404(Mood, pk=pk)
        tenant = get_tenant(req)

        try:
            session, recs = generate_session_recommendations(
                user=req.user,
                mood=mood
            )
        except Exception:
            logger.error("Recommendation failed", exc_info=True)
            return Response({"error": "Recommendation failed"}, status=500)

        if not recs:
            return Response({"error": "No recommendations"}, status=400)

        songs = [r.song for r in recs]

        response_text = get_mood_response(mood.name)

        session.response = response_text
        session.save()

        return Response({
            "mood": mood.name,
            "message": response_text,
            "songs": SongSerializer(songs, many=True).data
        })


# -------------------------
# SONG INTERACTION
# -------------------------

class SongViewSet(viewsets.ViewSet):

    def list(self, req):
        songs = Song.objects.filter(is_available=True)
        return Response(SongSerializer(songs, many=True).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def interact(self, req, pk=None):

        song = get_object_or_404(Song, pk=pk)
        tenant = get_tenant(req)

        action_type = req.data.get("action")

        if action_type not in ["play", "skip", "like"]:
            return Response({"error": "Invalid action"}, status=400)

        session = MoodSession.objects.filter(
            user=req.user,
            tenant=tenant
        ).order_by("-generated_at").first()

        if not session:
            return Response({"error": "No active session"}, status=400)

        interaction, _ = UserSongInteraction.objects.get_or_create(
            user=req.user,
            tenant=tenant,
            song=song,
            mood=session.mood
        )

        if action_type == "play":
            interaction.play_count += 1
        elif action_type == "skip":
            interaction.skipped_count += 1
        elif action_type == "like":
            interaction.liked = True

        interaction.save()

        return Response({"message": "Interaction recorded"})