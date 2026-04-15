from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from app.models import Tenant, Profile

User = get_user_model()


@transaction.atomic
def create_tenant_with_admin(*, tenant_name, username, email, password):

    # Normalize input
    tenant_name = tenant_name.strip()
    username = username.strip()
    email = email.strip().lower()

    # Validate
    if Tenant.objects.filter(name__iexact=tenant_name).exists():
        raise ValidationError("Tenant already exists")

    # Validate user
    if User.objects.filter(username=username).exists():
        raise ValidationError("Username already taken")

    if User.objects.filter(email=email).exists():
        raise ValidationError("Email already registered")

    # Create
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