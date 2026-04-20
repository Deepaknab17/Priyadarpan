import uuid
from rest_framework.response import Response
from django.utils import timezone
from app.models import Invite
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError

def create_invite(req):
    if req.method != "POST":
        return Response({"error": "Invalid method"}, status=405)

    if not req.user.is_authenticated or req.user.profile.role != "admin":
        return Response({"error": "Unauthorized"}, status=403)

    email = req.POST.get("email")
    email = (req.POST.get("email") or "").strip().lower()

    if not email:
        return Response({"error": "Email required"}, status=400)

    tenant = req.user.profile.tenant

    # prevent duplicate invite
    if Invite.objects.filter(email=email, tenant=tenant, used=False).exists():
        return Response({"error": "Invite already sent"}, status=400)

    token = str(uuid.uuid4())

    invite = Invite.objects.create(
        email=email,
        tenant=tenant,
        token=token
    )

    # you can send email later, for now just return link
    signup_link = f"http://127.0.0.1:8000/signup/?token={token}"

    return Response({
        "message": "Invite created",
        "signup_link": signup_link
    })

def signup_with_invite(req):
    token = req.GET.get("token")

    if not token:
        return render(req, "error.html", {"error": "Invalid invite link"})

    invite = Invite.objects.filter(token=token).first()

    if not invite:
        return render(req, "error.html", {"error": "Invalid invite"})

    if invite.used:
        return render(req, "error.html", {"error": "Invite already used"})

    # expiry check (2 days)
    if invite.created_at < timezone.now() - timedelta(days=2):
        return render(req, "error.html", {"error": "Invite expired"})

    if req.method == "POST":
        username = (req.POST.get("username") or "").strip()
        email = (req.POST.get("email") or "").strip().lower()
        password = req.POST.get("password")
        if not username or not password:
            return render(req, "signup.html", {
                "error": "Username and password required",
                 "token": token
    })

        #  email must match invite
        if email != invite.email:
            return render(req, "signup.html", {
                "error": "Email does not match invite",
                "token": token
            })

        # validate uniqueness
        if User.objects.filter(username=username).exists():
            return render(req, "signup.html", {
                "error": "Username already taken",
                "token": token
            })

        if User.objects.filter(email=email).exists():
            return render(req, "signup.html", {
                "error": "Email already registered",
                "token": token
            })

        # create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # attach profile (IMPORTANT — no new profile creation)
        profile = user.profile
        profile.role = "user"
        profile.tenant = invite.tenant
        profile.save()

        # mark invite used
        invite.used = True
        invite.save()

        login(req, user)

        return redirect("user_dashboard")

    return render(req, "signup.html", {"token": token})

def list_invites(req):
    if not req.user.is_authenticated or req.user.profile.role != "admin":
        return Response({"error": "Unauthorized"}, status=403)

    tenant = req.user.profile.tenant

    invites = Invite.objects.filter(tenant=tenant).values(
        "email", "used", "created_at"
    )

    return Response(list(invites))