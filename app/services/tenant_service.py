from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from app.models import Tenant, Profile

User = get_user_model()


@transaction.atomic
def create_tenant_with_admin(*, tenant_name, username, email, password):
    # Normalize input
    tenant_name = (tenant_name or "").strip()
    username = (username or "").strip()
    email = (email or "").strip().lower()
    # Validate required fields
    if not tenant_name:
        raise ValidationError("Tenant name required")
    if not username:
        raise ValidationError("Username required")
    if not email:
        raise ValidationError("Email required")
    if not password:
        raise ValidationError("Password required")
    # Validate uniqueness
    if Tenant.objects.filter(name__iexact=tenant_name).exists():
        raise ValidationError("Tenant already exists")
    if User.objects.filter(username=username).exists():
        raise ValidationError("Username already taken")
    if User.objects.filter(email=email).exists():
        raise ValidationError("Email already registered")
    # Create tenant
    tenant = Tenant.objects.create(name=tenant_name)
    # Create user
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password
    )
    # Create profile
    Profile.objects.create(
        user=user,
        role="admin",
        tenant=tenant
    )
    return user, tenant