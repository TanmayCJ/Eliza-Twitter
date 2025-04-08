from django.urls import path
from .views import PopularityScoreView, SafetyScoreView

urlpatterns = [
    path('popularity/', PopularityScoreView.as_view(), name='popularity-score'),
    path('safety/', SafetyScoreView.as_view(), name='safety-score'),
]