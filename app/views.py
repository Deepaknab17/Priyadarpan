from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets, status
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from payments.models import Payment
import requests, urllib.parse
from django.conf import settings
from app.services.recomendation_service import generate_session_recommendations
from .models import Memory, Mood, Song, MoodSession, SessionRecommendation, UserSongInteraction,Profile,Tenant
from .serializers import RegisterSerializer, MemorySerializer, MoodSerializer, SongSerializer, TenantSignupSerializer
from .services.mood_engine import get_mood_response
from app.services.spotify_service import search_tracks
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect


# -------------------------
# Helper
# -------------------------
def get_tenant(req):
    return req.user.profile.tenant
# -------------------------
# SuperAdmin
# -------------------------

def superadmin_dashboard(req):
    if not req.user.is_authenticated or req.user.profile.role != "superadmin":
        return Response({"error": "Unauthorized"}, status=403)

    return Response({
        "total_users": User.objects.count(),
        "total_admins": Profile.objects.filter(role="admin").count(),
        "total_tenants": Tenant.objects.count(),
        "total_songs": Song.objects.count(),
        "total_revenue": Payment.objects.filter(paid=True).count(),
        "active_premium_users": Profile.objects.filter(
            premium_until__gt=timezone.now()
        ).count()
    })


# -------------------------
# Spotify Login
# -------------------------
def spotify_login(request):
    scope = "user-read-private user-read-email playlist-read-private playlist-read-collaborative"
    params = {
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "scope": scope,
    }
    auth_url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(params)
    return redirect(auth_url)


# -------------------------
# Spotify Callback
# -------------------------
def spotify_callback(request):
    code = request.GET.get("code")

    if not code:
        return Response({"error": "No authorization code received"}, status=400)

    token_url = "https://accounts.spotify.com/api/token"

    response = requests.post(
        token_url,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
            "client_id": settings.SPOTIFY_CLIENT_ID,
            "client_secret": settings.SPOTIFY_CLIENT_SECRET,
        },
    )

    token_data = response.json()
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")

    if not access_token:
        return Response({ 
            "error": "Failed to obtain access token",
            "details": token_data
        })

    request.session["access_token"] = access_token
    request.session["refresh_token"] = refresh_token

    return Response({  
        "message": "Spotify connected successfully",
        "access_token": access_token,
        "refresh_token": refresh_token
    })


# -------------------------
# Spotify Test
# -------------------------

def test_spotify_tracks(request):

    access_token = request.session.get("access_token")

    if not access_token:
        return Response({"error": "No access token"})

    tracks = search_tracks(access_token, "happy")

    return Response({  
        "count": len(tracks),
        "tracks": tracks[:5]
    })


# -------------------------
# Tenant Signup
# -------------------------
class TenantSignupView(APIView):

    def post(self, request):
        serializer = TenantSignupSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {"message": "Tenant and admin created successfully"},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------------
# CHECK PREMIUM
# -------------------------

def check_premium(req):
    if req.user.is_authenticated:
        return Response({  
            "premium": req.user.profile.is_premium_active
        })

    return Response({"premium": False}) 


# -------------------------
# LIST SONGS
# -------------------------

def list_songs(req):
    songs = Song.objects.filter(is_available=True).values(
        "id",
        "title",
        "external_id",
        "is_premium"
    )

    return Response(list(songs))


# -------------------------
# PLAY SONG
# -------------------------

def play_song(req, song_id):
    song = get_object_or_404(Song, id=song_id)

    if song.is_premium:
        if not req.user.is_authenticated or not req.user.profile.is_premium_active:
            return Response({"error": "Premium required"}, status=403)  

    return Response({  
        "song": song.title,
        "message": "Playing song"
    })
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
def superadmin_dashboard(req):
    if req.user.profile.role != "superadmin":
        return redirect("login")

    return render(req, "superadmin.html")

def admin_dashboard(req):
    if req.user.profile.role != "admin":
        return redirect("login")

    return render(req, "admin.html")

def user_dashboard(req):
    if req.user.profile.role != "user":
        return redirect("login")

    return render(req, "user.html")