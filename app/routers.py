from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'memories', MemoryViewSet, basename='memory')
router.register(r'moods', MoodViewSet, basename='mood')
router.register(r'songs', SongViewSet, basename='song')

urlpatterns = router.urls