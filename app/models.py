from django.db import models
from django.contrib.auth.models import User


# -------------------------
# Mood
# -------------------------
class Mood(models.Model):

    name = models.CharField(max_length=50, unique=True)

    description = models.TextField(blank=True)

    # emotional space (2D model)
    valence = models.FloatField(db_index=True)   # sadness (-1) → happiness (+1)
    energy = models.FloatField(db_index=True)    # calm (0) → intense (1)

    def __str__(self):
        return self.name


# -------------------------
# Artist
# -------------------------
class Artist(models.Model):

    name = models.CharField(max_length=200, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# -------------------------
# Song
# -------------------------
class Song(models.Model):

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

    moods = models.ManyToManyField(
        Mood,
        related_name="songs"
    )

    # emotional coordinates
    valence = models.FloatField(
        null=True,
        db_index=True
    )

    energy = models.FloatField(
        null=True,
        db_index=True
    )

    is_available = models.BooleanField(
        default=True,
        db_index=True
    )

    duration_seconds = models.IntegerField(
        null=True,
        blank=True
    )

    play_count = models.IntegerField(default=0)

    last_synced = models.DateTimeField(auto_now=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        artists = ", ".join([a.name for a in self.artists.all()])
        return f"{self.title} - {artists}"


# -------------------------
# Memory
# -------------------------
class Memory(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="memories"
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

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.song.title}"


# -------------------------
# User Interaction
# -------------------------
class UserSongInteraction(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_index=True
    )

    song = models.ForeignKey(
        Song,
        on_delete=models.CASCADE,
        db_index=True
    )

    mood = models.ForeignKey(
        Mood,
        on_delete=models.CASCADE
    )

    play_count = models.IntegerField(default=0)

    skipped_count = models.IntegerField(default=0)

    liked = models.BooleanField(default=False)

    last_played = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        unique_together = ("user", "song", "mood")


# -------------------------
# Mood Session
# -------------------------
class MoodSession(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_index=True
    )

    mood = models.ForeignKey(
        Mood,
        on_delete=models.CASCADE
    )

    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-generated_at"]

    def __str__(self):
        return f"{self.user.username} - {self.mood.name} session"


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
        unique_together = ("session", "song")
        ordering = ["rank"]