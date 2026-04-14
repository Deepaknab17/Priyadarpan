import razorpay, razorpay.errors
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.mail import send_mail

from rest_framework.response import Response

from payments.models import Payment
from .models import Song, Profile, Tenant


# -------------------------
# LOGIN
# -------------------------
def login_view(req):
    if req.method == "POST":
        email = req.POST.get("email")
        password = req.POST.get("password")

        user = authenticate(req, username=email, password=password)

        if user is None:
            return render(req, "login.html", {"error": "Invalid credentials"})

        login(req, user)

        role = user.profile.role

        if role == "superadmin":
            return redirect("superadmin_dashboard")

        elif role == "admin":
            return redirect("admin_dashboard")

        else:
            return redirect("user_dashboard")

    return render(req, "login.html")


# -------------------------
# HTML DASHBOARDS
# -------------------------
def superadmin_dashboard(req):
    if not req.user.is_authenticated or req.user.profile.role != "superadmin":
        return redirect("login")
    return render(req, "superadmin.html")


def admin_dashboard(req):
    if not req.user.is_authenticated or req.user.profile.role != "admin":
        return redirect("login")
    return render(req, "admin.html")


def user_dashboard(req):
    if not req.user.is_authenticated or req.user.profile.role != "user":
        return redirect("login")
    return render(req, "user.html")


# -------------------------
# DASHBOARD APIs
# -------------------------
def superadmin_dashboard_api(req):
    if not req.user.is_authenticated or req.user.profile.role != "superadmin":
        return Response({"error": "Unauthorized"}, status=403)

    return Response({
        "total_users": User.objects.count(),
        "total_admins": Profile.objects.filter(role="admin").count(),
        "total_tenants": Tenant.objects.count(),
        "total_songs": Song.objects.count(),
        "total_payments": Payment.objects.filter(paid=True).count(),
        "active_premium_users": Profile.objects.filter(
            premium_until__gt=timezone.now()
        ).count()
    })


def admin_dashboard_api(req):
    if not req.user.is_authenticated or req.user.profile.role != "admin":
        return Response({"error": "Unauthorized"}, status=403)

    tenant = req.user.profile.tenant

    return Response({
        "tenant": tenant.name,
        "total_users": tenant.users.count(),
        "premium_users": tenant.users.filter(
            premium_until__gt=timezone.now()
        ).count(),
        "songs": Song.objects.filter(is_available=True).count()
    })


def user_dashboard_api(req):
    if not req.user.is_authenticated:
        return Response({"error": "Unauthorized"}, status=403)

    profile = req.user.profile

    return Response({
        "username": req.user.username,
        "premium": profile.is_premium_active,
        "premium_until": profile.premium_until
    })


# -------------------------
# SONG APIs
# -------------------------
def list_songs(req):
    songs = Song.objects.filter(is_available=True).values(
        "id",
        "title",
        "external_id",
        "is_premium"
    )
    return Response(list(songs))


def play_song(req, song_id):
    song = get_object_or_404(Song, id=song_id)

    if song.is_premium:
        if not req.user.is_authenticated or not req.user.profile.is_premium_active:
            return Response({"error": "Premium required"}, status=403)

    return Response({
        "song": song.title,
        "message": "Playing song"
    })


# -------------------------
# PREMIUM CHECK
# -------------------------
def check_premium(req):
    if req.user.is_authenticated:
        return Response({
            "premium": req.user.profile.is_premium_active
        })
    return Response({"premium": False})


# -------------------------
# PAYMENT (ACTIVATE PREMIUM + EMAIL)
# -------------------------
def verify_payment(req):
    import json
    data = json.loads(req.body)

    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_signature = data.get('razorpay_signature')

    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        return Response({"status": "failed"})

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY, settings.RAZORPAY_SECRET))

    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        })
    except razorpay.errors.SignatureVerificationError:
        return Response({"status": "failed"})

    payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)

    if not payment.paid:
        payment.razorpay_payment_id = razorpay_payment_id
        payment.paid = True
        payment.save()

        if payment.user:
            profile = payment.user.profile

            if profile.premium_until and profile.premium_until > timezone.now():
                profile.premium_until += timedelta(days=30)
            else:
                profile.premium_until = timezone.now() + timedelta(days=30)

            profile.save()

            #  EMAIL
            send_mail(
                subject="Premium Activated",
                message=f"Hi {payment.user.username}, your premium is now active!",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[payment.user.email],
                fail_silently=True,
            )

    return Response({"status": "success"})