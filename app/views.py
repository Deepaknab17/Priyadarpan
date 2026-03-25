from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.views import APIView
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
import requests, urllib.parse
from django.conf import settings
from .models import Memory, Mood, Song, MoodSession, SessionRecommendation
from .serializers import RegisterSerializer, MemorySerializer, MoodSerializer, SongSerializer
from .services.recomendation_service import generate_session_recomendations
from .services.mood_engine import detect_mood, get_mood_response
# -------------------------
# Helper
# -------------------------
def get_tenant(req):
    return req.user.profile.tenant


# -------------------------
# Mood Analyze 
# -------------------------
class MoodAnalyzeView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        text = request.data.get("text")

        if not text:
            return Response({"error": "Text is required"}, status=400)

        tenant = get_tenant(request)

        # 🔥 Get last session
        last_session = (
            MoodSession.objects
            .filter(user=request.user, tenant=tenant)
            .order_by("-generated_at")
            .first()
        )

        # 🔍 Detect mood (use your engine properly)
        mood_name = detect_mood(text, last_session)
        mood = get_object_or_404(Mood, name=mood_name)

        # 💬 Generate response
        response_text = get_mood_response(mood.name)

        # 🎵 Generate recommendations
        session, recs = generate_session_recommendations(
            user=request.user,
            mood=mood,
            tenant=tenant
        )

        songs = [rec.song for rec in recs]
        serializer = SongSerializer(songs, many=True)

        # 💾 Save emotional context
        session.input_text = text
        session.response = response_text
        session.save()

        return Response({
            "mood": mood.name,
            "message": response_text,
            "songs": serializer.data
        })


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

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def experience(self, req, pk=None):

        mood = self.get_object(pk)
        tenant = get_tenant(req)

        #  Check cached session
        session = (
            MoodSession.objects
            .filter(user=req.user, tenant=tenant, mood=mood)
            .order_by("-generated_at")
            .first()
        )

        if (
            session and
            timezone.now() - session.generated_at < timedelta(minutes=30) and
            session.recommendations.exists()
        ):
            recommendations = (
                session.recommendations
                .select_related("song")
                .order_by("rank")
            )

            songs = [rec.song for rec in recommendations]
            serializer = SongSerializer(songs, many=True)

            return Response({
                "mood": mood.name,
                "message": session.response,
                "songs": serializer.data,
                "cached": True
            })

        #  Generate new session
        session, recs = generate_session_recommendations(
            user=req.user,
            mood=mood,
            tenant=tenant
        )

        songs = [rec.song for rec in recs]
        serializer = SongSerializer(songs, many=True)

        response_text = get_mood_response(mood.name)

        session.response = response_text
        session.save()

        return Response({
            "mood": mood.name,
            "message": response_text,
            "songs": serializer.data,
            "cached": False
        })


# -------------------------
# Song ViewSet (FIXED)
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

        serializer = SongSerializer(songs, many=True)
        return Response(serializer.data)

    def retrieve(self, req, pk=None):
        song = self.get_object(pk)
        serializer = SongSerializer(song)
        return Response(serializer.data)