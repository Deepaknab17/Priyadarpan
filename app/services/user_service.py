from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from app.models import Profile

User = get_user_model()


@transaction.atomic
def create_user_with_profile(*, username, email, password, role, tenant=None):

    # Normalize
    username = (username or "").strip()
    email = (email or "").strip().lower()

    # Validate required fields
    if not username:
        raise ValidationError("Username required")

    if not email:
        raise ValidationError("Email required")

    if not password:
        raise ValidationError("Password required")

    if not role:
        raise ValidationError("Role required")

    # Validate role
    VALID_ROLES = ["superadmin", "admin", "user"]
    if role not in VALID_ROLES:
        raise ValidationError("Invalid role")

    # Tenant rules
    if role in ["admin", "user"] and not tenant:
        raise ValidationError("Admin/User must belong to a tenant")

    if role == "superadmin" and tenant:
        raise ValidationError("Superadmin cannot have a tenant")
    # Uniqueness
    if User.objects.filter(username=username).exists():
        raise ValidationError("Username already taken")

    if User.objects.filter(email=email).exists():
        raise ValidationError("Email already registered")

    # Create user
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password
    )
    # Create profile
    Profile.objects.create(
        user=user,
        role=role,
        tenant=tenant
    )
    return user