from django.contrib import admin
from .models import Mood, Song, Memory,MoodSession,SessionRecommendation

# Register your models here.
admin.site.register(Mood)
admin.site.register(Song)
admin.site.register(Memory)
admin.site.register(MoodSession)
admin.site.register(SessionRecommendation)


