from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import viewsets, status
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
import requests, urllib.parse

from django.conf import settings

from app.services.recomendation_service import generate_session_recommendations
from .models import Memory, Mood, Song, MoodSession, SessionRecommendation, UserSongInteraction
from .serializers import RegisterSerializer, MemorySerializer, MoodSerializer, SongSerializer
from .services.mood_engine import get_mood_response


# -------------------------
# Helper
# -------------------------
def get_tenant(req):
    return req.user.profile.tenant


# -------------------------
# Spotify Login
# -------------------------
def spotify_login(request):
    scope = "user-read-private user-read-email playlist-read-private playlist-read-collaborative"

    params = {
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "scope": scope,
    }

    auth_url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(params)
    return redirect(auth_url)


# -------------------------
# Spotify Callback
# -------------------------
def spotify_callback(request):
    code = request.GET.get("code")
    if not code:
        return JsonResponse({"error": "No authorization code received"}, status=400)

    token_url = "https://accounts.spotify.com/api/token"

    response = requests.post(
        token_url,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
            "client_id": settings.SPOTIFY_CLIENT_ID,
            "client_secret": settings.SPOTIFY_CLIENT_SECRET,
        },
    )
    token_data = response.json()
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    if not access_token:
        return JsonResponse({
            "error": "Failed to obtain access token",
            "details": token_data
        })
    request.session["access_token"] = access_token
    request.session["refresh_token"] = refresh_token
    return JsonResponse({
        "message": "Spotify connected successfully",
        "access_token": access_token,
        "refresh_token": refresh_token
    })
# -------------------------
# Auth Test
# -------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def protected_test(req):
    return Response({
        "message": "You are authenticated",
        "user": req.user.username
    })
# -------------------------
# Register User
# -------------------------
@api_view(["POST"])
def register_user(req):
    serializer = RegisterSerializer(data=req.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "User created successfully"},
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# -------------------------
# Memory ViewSet
# -------------------------
class MemoryViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    def get_object(self, pk, user):
        return get_object_or_404(
            Memory.objects.select_related("song"),
            pk=pk,
            user=user,
            tenant=user.profile.tenant
        )
    def list(self, req):
        memories = (
            Memory.objects
            .filter(user=req.user, tenant=get_tenant(req))
            .select_related("song")
        )
        return Response(MemorySerializer(memories, many=True).data)

    def create(self, req):

        serializer = MemorySerializer(data=req.data)

        if serializer.is_valid():
            serializer.save(user=req.user, tenant=get_tenant(req))
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, req, pk=None):

        memory = self.get_object(pk, req.user)
        return Response(MemorySerializer(memory).data)

    def destroy(self, req, pk=None):

        memory = self.get_object(pk, req.user)
        memory.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# -------------------------
# Mood ViewSet
# -------------------------
class MoodViewSet(viewsets.ViewSet):

    def get_object(self, pk):
        return get_object_or_404(Mood, pk=pk)

    def list(self, req):
        moods = Mood.objects.all()
        return Response(MoodSerializer(moods, many=True).data)

    def retrieve(self, req, pk=None):
        mood = self.get_object(pk)
        return Response(MoodSerializer(mood).data)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def experience(self, req, pk=None):

        mood = self.get_object(pk)
        tenant = get_tenant(req)

        session = (
            MoodSession.objects
            .filter(user=req.user, tenant=tenant, mood=mood)
            .order_by("-generated_at")
            .first()
        )

        # ✅ Cached session
        if (
            session and
            timezone.now() - session.generated_at < timedelta(minutes=30) and
            session.recommendations.exists()
        ):
            songs = [
                rec.song
                for rec in session.recommendations.all().order_by("rank")
            ]

            return Response({
                "mood": mood.name,
                "message": session.response,
                "songs": SongSerializer(songs, many=True).data,
                "cached": True
            })

        # 🚀 Generate new session
        session, recs = generate_session_recommendations(
            user=req.user,
            mood=mood,
            tenant=tenant
        )

        songs = [rec.song for rec in recs]

        response_text = get_mood_response(mood.name)

        session.response = response_text
        session.save()

        return Response({
            "mood": mood.name,
            "message": response_text,
            "songs": SongSerializer(songs, many=True).data,
            "cached": False
        })


# -------------------------
# Song ViewSet
# -------------------------
class SongViewSet(viewsets.ViewSet):

    def get_object(self, pk):
        return get_object_or_404(Song, pk=pk)

    def list(self, req):

        songs = Song.objects.filter(is_available=True)

        mood_id = req.query_params.get("mood")

        if mood_id:
            mood = get_object_or_404(Mood, id=mood_id)

            songs = songs.filter(
                valence__range=(mood.valence - 0.1, mood.valence + 0.1),
                energy__range=(mood.energy - 0.1, mood.energy + 0.1)
            )

        return Response(SongSerializer(songs, many=True).data)

    def retrieve(self, req, pk=None):

        song = self.get_object(pk)
        return Response(SongSerializer(song).data)

    # 🔥 Interaction API (IMPORTANT)
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def interact(self, req, pk=None):

        song = self.get_object(pk)
        tenant = get_tenant(req)

        action_type = req.data.get("action")

        if action_type not in ["play", "skip", "like"]:
            return Response({"error": "Invalid action"}, status=400)

        session = (
            MoodSession.objects
            .filter(user=req.user, tenant=tenant)
            .order_by("-generated_at")
            .first()
        )

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
            interaction.last_played = timezone.now()

        elif action_type == "skip":
            interaction.skipped_count += 1

        elif action_type == "like":
            interaction.liked = True

        interaction.save()

        return Response({"message": "Interaction recorded"})


# -------------------------
# Spotify Test
# -------------------------
from app.services.spotify_service import search_tracks

def test_spotify_tracks(request):

    access_token = request.session.get("access_token")

    if not access_token:
        return JsonResponse({"error": "No access token"})

    tracks = search_tracks(access_token, "happy")

    return JsonResponse({
        "count": len(tracks),
        "tracks": tracks[:5]
    })