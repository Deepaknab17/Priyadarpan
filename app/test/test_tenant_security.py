from django.test import TestCase
from django.core.exceptions import ValidationError

from app.models import (
    Tenant
)
from app.services.tenant_service import (
    create_tenant_with_admin
)

class TenantServiceTest(TestCase):
    def test_create_tenant_with_admin(self):

        user, tenant = (
            create_tenant_with_admin(
                tenant_name="Music Corp",
                username="admin1",
                email="admin@test.com",
                password="pass123"
            )
        )
        self.assertEqual(
            tenant.name,
            "Music Corp"
        )
        self.assertEqual(
            user.profile.role,
            "admin"
        )
        self.assertEqual(
            user.profile.tenant,
            tenant
        )
    def test_duplicate_tenant_fails(self):
        create_tenant_with_admin(
            tenant_name="Music Corp",
            username="admin1",
            email="admin@test.com",
            password="pass123"
        )
        with self.assertRaises(
            ValidationError
        ):
            create_tenant_with_admin(
                tenant_name="Music Corp",
                username="admin2",
                email="admin2@test.com",
                password="pass123"
            )
    def test_duplicate_email_fails(self):
        create_tenant_with_admin(
            tenant_name="Music Corp",
            username="admin1",
            email="admin@test.com",
            password="pass123"
        )
        with self.assertRaises(
            ValidationError
        ):
         create_tenant_with_admin(
                tenant_name="Another Corp",
                username="admin2",
                email="admin@test.com",
                password="pass123"
            )
    def test_blank_tenant_name_fails(self):
        with self.assertRaises(
            ValidationError
        ):
            create_tenant_with_admin(tenant_name="",username="admin1",email="admin@test.com",password="pass123")
                
                
                
                
          