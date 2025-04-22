from django.urls import path
from .views import PopularityScoreView, SafetyScoreView, CompareHashtagsView

urlpatterns = [
    path('popularity/', PopularityScoreView.as_view(), name='popularity-score'),
    path('safety/', SafetyScoreView.as_view(), name='safety-score'),
    path('compare_hashtags/', CompareHashtagsView.as_view(), name='compare-hashtags'),
]