from django.utils import timezone
from datetime import timedelta


def activate_premium(profile, days=30):
    if not profile:
        raise ValueError("Profile required")
    if days <= 0:
        raise ValueError("Days must be positive")
    now = timezone.now()
    if profile.premium_until and profile.premium_until > now:
        new_expiry = profile.premium_until + timedelta(days=days)
    else:
        new_expiry = now + timedelta(days=days)
    profile.premium_until = new_expiry
    profile.save()
    return new_expiry