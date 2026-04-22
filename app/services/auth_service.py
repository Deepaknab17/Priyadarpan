from django.core.mail import send_mail
from django.conf import settings
from app.models import PasswordResetToken
from django.contrib.auth import get_user_model

User = get_user_model()


def request_password_reset(email):

    email = (email or "").strip().lower()

    print("Function called with email:", email)

    user = User.objects.filter(email=email).first()

    print("USER:", user)

    if not user:
        return

    # invalidate old tokens
    PasswordResetToken.objects.filter(
        email=email,
        used=False
    ).update(used=True)

    token_obj = PasswordResetToken.objects.create(email=email)

    print("TOKEN:", token_obj.token)

    reset_link = (
        f"http://127.0.0.1:8000/reset-password/"
        f"?token={token_obj.token}"
    )

    print("ABOUT TO SEND EMAIL")
    print("BACKEND:", settings.EMAIL_BACKEND)

    send_mail(
        subject="Password Reset",
        message=(
            "You requested a password reset.\n\n"
            f"Click the link below:\n{reset_link}\n\n"
            "If you didn't request this, ignore this email."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False
    )


def reset_password(token, new_password):

    token = (token or "").strip()

    token_obj = PasswordResetToken.objects.filter(
        token=token
    ).first()

    if not token_obj:
        raise ValueError("Invalid token")

    if token_obj.used:
        raise ValueError("Token already used")

    if token_obj.is_expired():
        raise ValueError("Token expired")

    user = User.objects.filter(
        email=token_obj.email
    ).first()

    if not user:
        raise ValueError("User not found")

    user.set_password(new_password)
    user.save()

    token_obj.used = True
    token_obj.save()