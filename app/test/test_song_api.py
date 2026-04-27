from django.utils import timezone
from datetime import timedelta

from app.test.base import BaseAPITestCase


class SongAPITest(BaseAPITestCase):

    def setUp(self):

        super().setUp()

        self.song.is_premium = True
        self.song.save()

    def test_normal_user_cannot_play_premium_song(self):

        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.get(
            f"/songs/{self.song.id}/play/"
        )

        self.assertEqual(
            response.status_code,
            403
        )

        self.assertEqual(
            response.data["error"],
            "Premium required"
        )
        
    def test_admin_can_play_premium_song(self):

        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(
            f"/songs/{self.song.id}/play/"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response.data["song"],
            self.song.title
        )

    def test_premium_user_can_play_premium_song(self):

        profile = self.user.profile

        profile.premium_until = (
            timezone.now() + timedelta(days=5)
        )

        profile.save()

        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.get(
            f"/songs/{self.song.id}/play/"
        )

        self.assertEqual(
            response.status_code,
            200
        )