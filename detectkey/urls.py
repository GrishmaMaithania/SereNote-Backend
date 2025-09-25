from django.urls import path
from .views import (
    DetectScaleView,
    DetectChordsView,
    detect_from_youtube_view,
    detect_chords_from_youtube_view,
)

urlpatterns = [
    path("detect-key/", DetectScaleView.as_view(), name="detect-key"),
    path("detect-chords/", DetectChordsView.as_view(), name="detect-chords"),
    path("detect-from-youtube/", detect_from_youtube_view, name="detect-from-youtube"),
    path("detect-chords-from-youtube/", detect_chords_from_youtube_view, name="detect-chords-from-youtube"),
]
