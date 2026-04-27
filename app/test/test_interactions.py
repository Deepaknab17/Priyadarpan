from app.test.base import BaseAPITestCase

from app.models import (
    MoodSession,
    UserSongInteraction
)


class InteractionAPITest(BaseAPITestCase):

    def setUp(self):

        super().setUp()

        self.session = MoodSession.objects.create(
            user=self.user,
            tenant=self.tenant,
            mood=self.mood
        )

    def test_play_interaction_increments_count(self):

        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.post(
            f"/songs/{self.song.id}/interact/",
            {
                "action": "play"
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        interaction = UserSongInteraction.objects.get(
            user=self.user,
            song=self.song
        )

        self.assertEqual(
            interaction.play_count,
            1
        )

    def test_invalid_action_returns_400(self):

        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.post(
            f"/songs/{self.song.id}/interact/",
            {
                "action": "dance"
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            400
        )

        self.assertEqual(
            response.data["error"],
            "Invalid action"
        )

    def test_interaction_requires_active_session(self):

        MoodSession.objects.all().delete()

        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.post(
            f"/songs/{self.song.id}/interact/",
            {
                "action": "play"
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            400
        )

        self.assertEqual(
            response.data["error"],
            "No active session"
        )