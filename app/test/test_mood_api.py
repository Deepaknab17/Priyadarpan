from unittest.mock import patch, Mock

from app.test.base import BaseAPITestCase


class MoodExperienceTest(BaseAPITestCase):

    @patch(
        "app.views.generate_session_recommendations"
    )
    def test_experience_returns_songs(
        self,
        mock_recommendations
    ):

        # AUTHENTICATE USER
        self.client.force_authenticate(
            user=self.user
        )

        # FAKE SESSION
        fake_session = Mock()

        # FAKE RECOMMENDATION
        fake_rec = Mock()

        # recommendation.song
        fake_rec.song = self.song

        # MOCK RETURN VALUE
        mock_recommendations.return_value = (
            fake_session,
            [fake_rec]
        )

        # CALL ENDPOINT
        response = self.client.get(
            f"/moods/{self.mood.id}/experience/"
        )

        # ASSERTIONS
        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response.data["mood"],
            self.mood.name
        )

        self.assertEqual(
            len(response.data["songs"]),
            1
        )

        self.assertEqual(
            response.data["songs"][0]["title"],
            self.song.title
        )