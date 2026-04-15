"""
URL configuration for project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from app.views import *
from payments.views import *
from app.routers import router
from app.services import invite_view


urlpatterns = [

    # -------------------------
    # ADMIN
    # -------------------------
    path('admin/', admin.site.urls),

    # -------------------------
    # MAIN ROUTER (ViewSets)
    # -------------------------
    path('', include(router.urls)),

    # -------------------------
    # JWT AUTH
    # -------------------------
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # -------------------------
    # TENANT (FIXED )
    # -------------------------
    path('tenant/signup/', TenantSignupView.as_view()),

    # -------------------------
    # SPOTIFY
    # -------------------------
    path('api/spotify/login/', spotify_login),
    path('api/spotify/callback/', spotify_callback),
    path('test-spotify/', test_spotify_tracks),

    # 🔥 NEW (you created this view but didn't wire it)
    path('spotify/ingest/', ingest_spotify_playlist),

    # -------------------------
    # PAYMENTS
    # -------------------------
    path('payments/', include("payments.urls")),

    # -------------------------
    # INVITE SYSTEM
    # -------------------------
    path('invite/create/', invite_view.create_invite),
    path('invite/list/', invite_view.list_invites),
    path('signup/', invite_view.signup_with_invite),

    # -------------------------
    # PREMIUM
    # -------------------------
    path('premium/check/', check_premium),

    # -------------------------
    # BASIC SONG APIs
    # -------------------------
    path('songs/list/', list_songs),
    path('songs/play/<int:song_id>/', play_song),

]    
# "key": "rzp_test_pr99iascS1WRtU",
#   