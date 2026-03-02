from django.shortcuts import render,redirect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework import status
from .models import Memory,Mood,Song
from rest_framework.viewsets import ReadOnlyModelViewSet
from .serializers import RegisterSerializer,MemorySerializer,MoodSerializer,SongSerializer

# Create your views here.


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_test(request):
    return Response({
        "message": "You are authenticated",
        "user": request.user.username
    })



@api_view(['POST'])
def register_user(request):
    serializer = RegisterSerializer(data=request.data)
    
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "User created successfully"},
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class MemoryViewSet(ModelViewSet):
    serializer_class = MemorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Memory.objects.filter(user=self.request.user).select_related('song')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
class MoodViewSet(ReadOnlyModelViewSet):
    queryset = Mood.objects.all()
    serializer_class = MoodSerializer
class SongViewSet(ReadOnlyModelViewSet):
    serializer_class = SongSerializer

    def get_queryset(self):
        queryset = Song.objects.select_related('mood')

        mood_id = self.request.query_params.get('mood')

        if mood_id:
            queryset = queryset.filter(mood_id=mood_id)

        return queryset