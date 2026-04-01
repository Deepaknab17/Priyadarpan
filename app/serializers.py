from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Memory, Mood, Song,Tenant
from .services.user_service import create_user_with_profile


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=["admin", "user", "superadmin"])
    tenant_id = serializers.IntegerField(required=False)

    class Meta:
        model = User
        fields = ("username", "email", "password", "role", "tenant_id")

    def create(self, validated_data):
        role = validated_data.pop("role")
        tenant_id = validated_data.pop("tenant_id", None)

        tenant = None
        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id)
            except Tenant.DoesNotExist:
                raise serializers.ValidationError("Invalid tenant")

        user = create_user_with_profile(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            role=role,
            tenant=tenant
        )

        return user


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