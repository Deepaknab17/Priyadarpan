from django.db import models
from django.contrib.auth.models import User
# -------------------------
# Tenant
# -------------------------
class Tenant(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name
# -------------------------
# Base Tenant Model
# -------------------------
class TenantModel(models.Model):
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        abstract = True
# -------------------------
# Profile (User → Tenant)
# -------------------------
class Profile(models.Model):

    ROLE_CHOICES = (
        ("admin", "Tenant Admin"),
        ("user", "User"),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="users",
        db_index=True
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="user"
    )

    def __str__(self):
        return f"{self.user.username} - {self.tenant.name}"


# -------------------------
# Mood (GLOBAL)
# -------------------------
class Mood(models.Model):

    name = models.CharField(max_length=50, unique=True)

    description = models.TextField(blank=True)

    valence = models.FloatField(db_index=True)

    energy = models.FloatField(db_index=True)

    def __str__(self):
        return self.name


# -------------------------
# Artist (GLOBAL)
# -------------------------
class Artist(models.Model):

    name = models.CharField(max_length=200, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# -------------------------
# Song (GLOBAL)
# -------------------------
class Song(models.Model):

    source = models.CharField(
        max_length=50,
        default="spotify"
    )

    external_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True
    )

    title = models.CharField(max_length=200)

    artists = models.ManyToManyField(
        Artist,
        related_name="songs"
    )

    valence = models.FloatField(
        null=True,
        db_index=True
    )

    energy = models.FloatField(
        null=True,
        db_index=True
    )

    duration_seconds = models.IntegerField(
        null=True,
        blank=True
    )

    is_available = models.BooleanField(
        default=True,
        db_index=True
    )

    play_count = models.PositiveIntegerField(default=0)

    last_synced = models.DateTimeField(auto_now=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["valence", "energy", "is_available"]),
        ]

    def __str__(self):
        return self.title


# -------------------------
# Memory (Tenant Scoped)
# -------------------------
class Memory(TenantModel):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="memories",
        db_index=True
    )

    song = models.ForeignKey(
        Song,
        on_delete=models.CASCADE,
        related_name="memories"
    )

    mood = models.ForeignKey(
        Mood,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    note = models.TextField()

    dedicated_to = models.CharField(
        max_length=200,
        blank=True
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]


# -------------------------
# User Interaction
# -------------------------
class UserSongInteraction(TenantModel):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_index=True
    )

    song = models.ForeignKey(
        Song,
        on_delete=models.CASCADE
    )

    mood = models.ForeignKey(
        Mood,
        on_delete=models.CASCADE
    )

    play_count = models.PositiveIntegerField(default=0)

    skipped_count = models.PositiveIntegerField(default=0)

    liked = models.BooleanField(default=False)

    last_played = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        unique_together = ("tenant", "user", "song", "mood")
        indexes = [
            models.Index(fields=["tenant", "user"]),
            models.Index(fields=["song"]),
        ]


# -------------------------
# Mood Session
# -------------------------
class MoodSession(TenantModel):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_index=True
    )

    mood = models.ForeignKey(
        Mood,
        on_delete=models.CASCADE,
        db_index=True,
        
    )
    input_text = models.TextField(null=True,
        blank=True,)
    response = models.TextField(
        null=True,
        blank=True,
    
    )


    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-generated_at"]


# -------------------------
# Session Recommendation
# -------------------------
class SessionRecommendation(models.Model):
    session = models.ForeignKey(
        MoodSession,
        on_delete=models.CASCADE,
        related_name="recommendations"
    )
    song = models.ForeignKey(
        Song,
        on_delete=models.CASCADE
    )
    rank = models.IntegerField()
    class Meta:
        ordering = ["rank"]
        unique_together = [
            ("session", "song"),
            ("session", "rank"),
        ]