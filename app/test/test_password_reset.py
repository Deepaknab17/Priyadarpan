from unittest.mock import patch
from django.contrib.auth.models import User
from app.test.base import BaseAPITestCase


class PasswordResetTest(BaseAPITestCase):
    @patch("app.views.request_password_reset")
    def test_request_reset_called(self,mock_reset):
        response = self.client.post("/request-reset/",{"email":"user@test.com"},format="json")
        self.assertEqual(response.status_code,200)
        mock_reset.assert_called_once_with("user@test.com")
    @patch("app.views.reset_password")

    def test_invalid_token_returns_400(self,mock_reset_password):
        # FORCE FAILURE
        mock_reset_password.side_effect = (Exception("Invalid token"))

        response = self.client.post("/reset-password/",{"token":"bad-token","password":"newpass123"},format="json")
        
        self.assertEqual(response.status_code,400)
        self.assertEqual(response.data["error"],"invalid token")
            
    