from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Memory,Mood,Song


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(username=validated_data['username'],email=validated_data['email'],password=validated_data['password'] )     
        return user
class MemorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Memory
        fields = ('id', 'song', 'note', 'dedicated_to', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')
class MoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mood
        fields = ('id', 'name', 'description')
class SongSerializer(serializers.ModelSerializer):
    mood= MoodSerializer(many=True, read_only=True)

    class Meta:
        model = Song
        fields = ('id', 'external_id', 'title', 'artist', 'moods')