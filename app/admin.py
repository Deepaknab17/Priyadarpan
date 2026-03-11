from django.contrib import admin
from .models import Mood, Song, Memory,MoodSession,SessionRecommendation,Tenant, Profile

# Register your models here.
admin.site.register(Mood)
admin.site.register(Song)
admin.site.register(Memory)
admin.site.register(MoodSession)
admin.site.register(SessionRecommendation)
admin.site.register(Tenant)
admin.site.register(Profile)



