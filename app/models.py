from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Mood(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Song(models.Model):
    external_id = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=200)
    artist = models.CharField(max_length=200)
    mood = models.ForeignKey(
        Mood,
        on_delete=models.CASCADE,
        related_name='songs'
    )

    def __str__(self):
        return f"{self.title} - {self.artist}"


class Memory(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='memories'
    )
    song = models.ForeignKey(
        Song,
        on_delete=models.CASCADE,
        related_name='memories'
    )
    note = models.TextField()
    dedicated_to = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'song')

    def __str__(self):
        return f"{self.user.username} - {self.song.title}"