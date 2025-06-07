from django.urls import path
from .views import (
    PopularityScoreView,
    CompareHashtagsView,
    SafetyScoreView, 
    TweetsView,
    LatestTweetView,
    SingleTweetView,
    ValidSendersView,
    EnvironmentalNewsView,
    ImageGenView,
    PersonalityAnalysisView,
    QueuedTweetsView,
    QueuedTweetDetailView
)

urlpatterns = [
    path('popularity/', PopularityScoreView.as_view(), name='popularity-score'),
    path('safety/', SafetyScoreView.as_view(), name='safety-score'),
    path('compare_hashtags/', CompareHashtagsView.as_view(), name='compare-hashtags'),

    path('tweets/', TweetsView.as_view(), name='tweets'),
    path('tweets/latest/', LatestTweetView.as_view(), name='latest-tweet'),
    path('tweets/senders/', ValidSendersView.as_view(), name='valid-senders'),
    path('tweets/<str:tweet_id>/', SingleTweetView.as_view(), name='tweet-detail'),

    path('news/', EnvironmentalNewsView.as_view(), name='environmental-news'),

    path('imagegen/', ImageGenView.as_view(), name='imagegen'),

    path('personality-analysis/', PersonalityAnalysisView.as_view(), name='personality-analysis'),

    path('queued-tweets/', QueuedTweetsView.as_view(), name='queued-tweets'),
    path('queued-tweets/<int:pk>/', QueuedTweetDetailView.as_view(), name='queued-tweet-detail')
]