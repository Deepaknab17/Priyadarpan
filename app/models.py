from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid
from datetime import timedelta

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
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


# -------------------------
# Profile
# -------------------------
class Profile(models.Model):
    ROLE_CHOICES = (
        ("superadmin", "SuperAdmin"),
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
        related_name="profiles",
        null=True,
        blank=True
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="user"
    )

    premium_until = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True  # 🔥 faster premium queries
    )

    def clean(self):
        if self.role == "superadmin" and self.tenant:
            raise ValidationError("Superadmin cannot have tenant")

        if self.role in ["admin", "user"] and not self.tenant:
            raise ValidationError("Admin/User must belong to a tenant")

    def save(self, *args, **kwargs):
        if self.role == "superadmin":
            self.tenant = None

        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_premium_active(self):
        return self.premium_until and self.premium_until > timezone.now()

    def __str__(self):
        return f"{self.user.username} - {self.role}"


# -------------------------
# Artist (GLOBAL)
# -------------------------
class Artist(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


# -------------------------
# Mood (GLOBAL)
# -------------------------
class Mood(models.Model):
    name = models.CharField(max_length=50, unique=True)
    valence = models.FloatField(db_index=True)
    energy = models.FloatField(db_index=True)

    def __str__(self):
        return self.name


# -------------------------
# Invite (TENANT CONTROL)
# -------------------------
class Invite(models.Model):
    email = models.EmailField()
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ("email", "tenant")
    def is_expired(self):
        from datetime import timedelta
        return self.created_at < timezone.now() - timedelta(days=2)
    def __str__(self):
        return f"{self.email} → {self.tenant.name}"


# -------------------------
# Song (GLOBAL CATALOG)
# -------------------------
class Song(models.Model):
    title = models.CharField(max_length=200)
    artists = models.ManyToManyField(Artist, related_name="songs")
    preview_url = models.URLField(null=True, blank=True)
    external_id = models.CharField(max_length=100,unique=True,db_index=True )
    valence = models.FloatField(null=True, db_index=True)
    energy = models.FloatField(null=True, db_index=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    is_premium = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    play_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.title


# -------------------------
# Memory (TENANT SCOPED)
# -------------------------
class Memory(TenantModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    mood = models.ForeignKey(Mood, null=True, blank=True, on_delete=models.SET_NULL)
    note = models.TextField()
    dedicated_to = models.CharField(max_length=200, blank=True)
    updated_at = models.DateTimeField(auto_now=True)


# -------------------------
# User Interaction (TENANT SCOPED)
# -------------------------
class UserSongInteraction(TenantModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    mood = models.ForeignKey(Mood, on_delete=models.CASCADE)
    play_count = models.PositiveIntegerField(default=0)
    skipped_count = models.PositiveIntegerField(default=0)
    liked = models.BooleanField(default=False)
    last_played = models.DateTimeField(null=True, blank=True)
    class Meta:
        unique_together = ("tenant", "user", "song", "mood")


# -------------------------
# Mood Session (TENANT SCOPED)
# -------------------------
class MoodSession(TenantModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mood = models.ForeignKey(Mood, on_delete=models.CASCADE)
    input_text = models.TextField(null=True, blank=True)
    response = models.TextField(null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

# -------------------------
# Recommendations (TENANT SAFE VIA SESSION)
# -------------------------
class SessionRecommendation(models.Model):
    session = models.ForeignKey(
        MoodSession,
        on_delete=models.CASCADE,
        related_name="recommendations"
    )
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    rank = models.IntegerField()
    
    class Meta:
        unique_together = ("session", "rank")

class PasswordResetToken(models.Model):
    email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    def is_expired(self):
        return self.created_at < timezone.now() - timedelta(hours=1)

    def __str__(self):
        return f"{self.email} - {self.token}"