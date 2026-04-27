from rest_framework.test import APITestCase
from django.contrib.auth.models import User

from app.models import (
    Tenant,
    Profile,
    Song,
    Mood
)


class BaseAPITestCase(APITestCase):

    def setUp(self):

        # TENANT
        self.tenant = Tenant.objects.create(
            name="Tenant A"
        )

        # USER
        self.user = User.objects.create_user(
            username="user1",
            password="testpass123"
        )

        Profile.objects.create(
            user=self.user,
            tenant=self.tenant,
            role="user"
        )

        # ADMIN
        self.admin = User.objects.create_user(
            username="admin1",
            password="adminpass123"
        )

        Profile.objects.create(
            user=self.admin,
            tenant=self.tenant,
            role="admin"
        )

        # SUPERADMIN
        self.superadmin = User.objects.create_user(
            username="superadmin",
            password="superpass123"
        )

        Profile.objects.create(
            user=self.superadmin,
            role="superadmin"
        )

        # MOOD
        self.mood = Mood.objects.create(
            name="Happy",
            valence=0.9,
            energy=0.8
        )

        # SONG
        self.song = Song.objects.create(
            title="Test Song",
            external_id="abc123",
            valence=0.7,
            energy=0.6,
            is_available=True
        )