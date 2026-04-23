from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Memory, Mood, Song,Tenant
from .services.user_service import create_user_with_profile
from .services.tenant_service import create_tenant_with_admin



class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=["admin", "user"])
    class Meta:
        model = User
        fields = ("username", "email", "password", "role")
    def create(self, validated_data):
        request = self.context["request"]
        #  Ensures only admin can create users
        
        if request.user.profile.role != "admin":
            raise serializers.ValidationError("Only admins can create users")
        role = validated_data.pop("role")

        # Tenant comes from admin
        tenant = request.user.profile.tenant
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
        fields = ["id", "name", "valence", "energy"]


class SongSerializer(serializers.ModelSerializer):
    artists = serializers.StringRelatedField(many=True)
    class Meta:
        model = Song
        fields = (
            "id",
            "external_id",
            "title",
            "artists",
            "valence",
            "energy",
            "duration_seconds",
            "play_count",
            "is_premium",
            "preview_url",
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
        fields = ( "id","song","song_id","mood","note","dedicated_to",
            
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

class TenantSignupSerializer(serializers.Serializer):
    tenant_name = serializers.CharField()
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def create(self, validated_data):
        user = create_tenant_with_admin(
            tenant_name=validated_data["tenant_name"],
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"]
        )
        return user