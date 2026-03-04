from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import viewsets, status
from django.http import Http404

from django.contrib.auth.models import User

from .models import Memory, Mood, Song
from .serializers import (
    RegisterSerializer,
    MemorySerializer,
    MoodSerializer,
    SongSerializer
)


# AUTH TEST
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_test(req):
    return Response({
        "message": "You are authenticated",
        "user": req.user.username
    })


# REGISTER USER
@api_view(['POST'])
def register_user(req):

    serializer = RegisterSerializer(data=req.data)

    if serializer.is_valid():
        serializer.save()
        return Response({"message": "User created successfully"},status=status.HTTP_201_CREATED )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# MEMORY VIEWSET
class MemoryViewSet(viewsets.ViewSet):

    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return Memory.objects.select_related('song').get(pk=pk, user=user)
        except Memory.DoesNotExist:
            raise Http404


    # GET /api/memories/
    def list(self, req):

        memories = Memory.objects.filter(
            user=req.user
        ).select_related('song')

        serializer = MemorySerializer(memories, many=True)

        return Response(serializer.data)


    # POST /api/memories/
    def create(self, req):

        serializer = MemorySerializer(data=req.data)

        if serializer.is_valid():

            serializer.save(user=req.user)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    # GET /api/memories/{id}/
    def retrieve(self, req, pk=None):

        memory = self.get_object(pk, req.user)

        serializer = MemorySerializer(memory)

        return Response(serializer.data)


    # DELETE /api/memories/{id}/
    def destroy(self, req, pk=None):

        memory = self.get_object(pk, req.user)

        memory.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


# MOOD VIEWSET
class MoodViewSet(viewsets.ViewSet):

    def get_object(self, pk):
        try:
            return Mood.objects.get(pk=pk)
        except Mood.DoesNotExist:
            raise Http404


    # GET /api/moods/
    def list(self, req):

        moods = Mood.objects.all()

        serializer = MoodSerializer(moods, many=True)

        return Response(serializer.data)


    # GET /api/moods/{id}/
    def retrieve(self, req, pk=None):

        mood = self.get_object(pk)

        serializer = MoodSerializer(mood)

        return Response(serializer.data)


    # GET /api/moods/{id}/songs/
    @action(detail=True, methods=['get'])
    def songs(self, req, pk=None):

        mood = self.get_object(pk)

        songs = Song.objects.filter(mood__id=pk,is_available=True ).prefetch_related('mood')

        serializer = SongSerializer(songs, many=True)

        return Response(serializer.data)


# SONG VIEWSET
class SongViewSet(viewsets.ViewSet):

    def get_object(self, pk):
        try:
            return Song.objects.prefetch_related('mood').get(pk=pk)
        except Song.DoesNotExist:
            raise Http404


    # GET /api/songs/
    def list(self, req):

        songs = Song.objects.prefetch_related('mood')

        mood_id = req.query_params.get('mood')

        if mood_id:
            songs = songs.filter(mood__id=mood_id)

        serializer = SongSerializer(songs, many=True)

        return Response(serializer.data)


    # GET /api/songs/{id}/
    def retrieve(self, req, pk=None):

        song = self.get_object(pk)

        serializer = SongSerializer(song)

        return Response(serializer.data)