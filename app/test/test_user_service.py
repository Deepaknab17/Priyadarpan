from django.test import TestCase
from django.core.exceptions import ValidationError

from app.models import (
    Tenant,
    Profile
)

from app.services.user_service import (
    create_user_with_profile
)


class UserServiceTest(TestCase):

    def setUp(self):

        self.tenant = Tenant.objects.create(
            name="Tenant A"
        )

    def test_create_normal_user(self):

        user = create_user_with_profile(
            username="john",
            email="john@test.com",
            password="pass123",
            role="user",
            tenant=self.tenant
        )

        self.assertEqual(
            user.username,
            "john"
        )

        self.assertEqual(
            user.profile.role,
            "user"
        )

        self.assertEqual(
            user.profile.tenant,
            self.tenant
        )

    def test_superadmin_cannot_have_tenant(self):

        with self.assertRaises(
            ValidationError
        ):

            create_user_with_profile(
                username="super",
                email="super@test.com",
                password="pass123",
                role="superadmin",
                tenant=self.tenant
            )

    def test_user_requires_tenant(self):

        with self.assertRaises(
            ValidationError
        ):

            create_user_with_profile(
                username="user1",
                email="user@test.com",
                password="pass123",
                role="user"
            )

    def test_invalid_role_fails(self):

        with self.assertRaises(
            ValidationError
        ):

            create_user_with_profile(
                username="bad",
                email="bad@test.com",
                password="pass123",
                role="king",
                tenant=self.tenant
            )

    def test_duplicate_email_fails(self):

        create_user_with_profile(
            username="john",
            email="john@test.com",
            password="pass123",
            role="user",
            tenant=self.tenant
        )

        with self.assertRaises(
            ValidationError
        ):

            create_user_with_profile(
                username="john2",
                email="john@test.com",
                password="pass123",
                role="user",
                tenant=self.tenant
            )