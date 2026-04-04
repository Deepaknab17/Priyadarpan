from django.utils import timezone
from datetime import timedelta

def activate_premium(profile, days=30):
    now = timezone.now()

    # If already active → extend
    if profile.premium_until and profile.premium_until > now:
        profile.premium_until += timedelta(days=days)
    else:
        profile.premium_until = now + timedelta(days=days)

    profile.save()