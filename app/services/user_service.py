from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from app.models import Profile

User = get_user_model()

def create_user_with_profile(*, username, email, password, role, tenant=None):
    if role in ["admin", "user"] and not tenant:
        raise ValidationError("Admin/User must belong to a tenant")

    if role == "superadmin" and tenant:
        raise ValidationError("Superadmin cannot have a tenant")

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password
    )

    Profile.objects.create(
        user=user,
        role=role,
        tenant=tenant
    )

    return user