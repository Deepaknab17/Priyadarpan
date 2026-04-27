from unittest.mock import patch
from app.test.base import BaseAPITestCase


class RateLimitTest(BaseAPITestCase):
    @patch("app.views.rate_limit")
    def test_mood_experience_rate_limited(
        self,
        mock_rate_limit
    ):

        mock_rate_limit.return_value = False

        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.get(
            f"/moods/{self.mood.id}/experience/"
        )

        self.assertEqual(
            response.status_code,
            429
        )

        self.assertEqual(
            response.data["error"],
            "Too many requests"
        )