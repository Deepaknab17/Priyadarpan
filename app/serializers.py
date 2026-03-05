from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Memory, Mood, Song


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("username", "email", "password")

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class MoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mood
        fields = ("id", "name", "description", "emotional_value")


class SongSerializer(serializers.ModelSerializer):
    moods = MoodSerializer(many=True, read_only=True)

    class Meta:
        model = Song
        fields = (
            "id",
            "external_id",
            "title",
            "artist",
            "emotional_value",
            "duration",
            "play_count",
            "moods",
        )


class MemorySerializer(serializers.ModelSerializer):

    song = SongSerializer(read_only=True)

    song_id = serializers.PrimaryKeyRelatedField(
        queryset=Song.objects.all(),
        source="song",
        write_only=True
    )

    mood = serializers.PrimaryKeyRelatedField(
        queryset=Mood.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Memory
        fields = (
            "id",
            "song",
            "song_id",
            "mood",
            "note",
            "dedicated_to",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")