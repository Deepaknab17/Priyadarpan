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
from app.services.recomendation_service import generate_session_recomendations
from .models import Memory, Mood, Song, MoodSession, SessionRecommendation
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
    scope= "user-read-private user-read-email playlist-read-private playlist-read-collaborative"
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
        return JsonResponse({"error": "Failed to obtain access token", "details": token_data})

    request.session["access_token"] = access_token
    request.session["refresh_token"] = refresh_token
    print("Callback hit")
    print(token_data)

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
            .filter(
                user=req.user,
                tenant=get_tenant(req)
            )
            .select_related("song")
        )

        serializer = MemorySerializer(memories, many=True)

        return Response(serializer.data)

    def create(self, req):

        serializer = MemorySerializer(data=req.data)

        if serializer.is_valid():

            serializer.save(
                user=req.user,
                tenant=get_tenant(req)
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, req, pk=None):

        memory = self.get_object(pk, req.user)

        serializer = MemorySerializer(memory)

        return Response(serializer.data)

    def destroy(self, req, pk=None):

        memory = self.get_object(pk, req.user)

        memory.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
# from django.http import JsonResponse
# from app.services.spotify_service import get_playlist_tracks


# def test_spotify_tracks(request):

#     access_token = request.session.get("access_token")

#     if not access_token:
#         return JsonResponse({"error": "No access token"})

#     playlist_id =  "37i9dQZF1DX4dyzvuaRJ0n"  # Spotify Top Hits

#     tracks = get_playlist_tracks(access_token, playlist_id)

#     return JsonResponse({
#         "count": len(tracks),
#         "tracks": tracks[:5]
#     })


# -------------------------
# Mood ViewSet
# -------------------------
class MoodViewSet(viewsets.ViewSet):

    def get_object(self, pk):

        return get_object_or_404(Mood, pk=pk)

    def list(self, req):

        moods = Mood.objects.all()

        serializer = MoodSerializer(moods, many=True)

        return Response(serializer.data)

    def retrieve(self, req, pk=None):

        mood = self.get_object(pk)

        serializer = MoodSerializer(mood)

        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def songs(self, req, pk=None):

        mood = self.get_object(pk)

        songs = (
            Song.objects
            .filter(moods=mood, is_available=True)
            .prefetch_related("moods")
        )

        serializer = SongSerializer(songs, many=True)

        return Response(serializer.data)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def experience(self, req, pk=None):

        mood = self.get_object(pk)

        session = (
            MoodSession.objects
            .filter(
                user=req.user,
                tenant=get_tenant(req),
                mood=mood
            )
            .order_by("-generated_at")
            .first()
        )

        if session and timezone.now() - session.generated_at < timedelta(minutes=30):

            recommendations = (
                session.recommendations
                .select_related("song")
                .order_by("rank")
            )

            songs = [rec.song for rec in recommendations]
            serializer = SongSerializer(songs, many=True)
            response_text = get_mood_response(mood.name)

            return Response({
                "mood": mood.name,
                "songs": serializer.data,
                "cached": True,
                response_text:True
            })

        session, recs = generate_session_recomendations(req.user, mood)

        songs = [rec.song for rec in recs]
        serializer = SongSerializer(songs, many=True)
        response_text = get_mood_response(mood.name)

        return Response({
            "mood": mood.name,
            "songs": serializer.data,
            "cached": False,
            response_text:False
        })


# -------------------------
# Song ViewSet
# -------------------------
class SongViewSet(viewsets.ViewSet):

    def get_object(self, pk):

        return get_object_or_404(
            Song.objects.prefetch_related("moods"),
            pk=pk
        )

    def list(self, req):

        songs = Song.objects.prefetch_related("moods")

        mood_id = req.query_params.get("mood")

        if mood_id:
            songs = songs.filter(moods__id=mood_id)

        serializer = SongSerializer(songs, many=True)

        return Response(serializer.data)

    def retrieve(self, req, pk=None):

        song = self.get_object(pk)

        serializer = SongSerializer(song)

        return Response(serializer.data)

from app.services.spotify_service import search_tracks

def test_spotify_tracks(request):

    access_token = request.session.get("access_token")

    tracks = search_tracks(access_token, "happy")

    return JsonResponse({
        "count": len(tracks),
        "tracks": tracks[:5]
    })