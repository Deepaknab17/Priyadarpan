from django.contrib import admin
from .models import Mood, Song, Memory

# Register your models here.
admin.site.register(Mood)
admin.site.register(Song)
admin.site.register(Memory)

