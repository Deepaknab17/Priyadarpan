from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from app.models import Tenant, Profile

User = get_user_model()

@transaction.atomic
def create_tenant_with_admin(*, tenant_name, username, email, password):
    
    # Prevent duplicate tenant
    if Tenant.objects.filter(name=tenant_name).exists():
        raise ValidationError("Tenant already exists")

    # Create tenant
    tenant = Tenant.objects.create(name=tenant_name)

    #  Create user
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password
    )

    # Create profile -> admin
    Profile.objects.create(
        user=user,
        role="admin",
        tenant=tenant
    )

    return user