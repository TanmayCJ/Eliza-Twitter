from django.urls import path
from .views import (
    PopularityScoreView, 
    SafetyScoreView, 
    CompareHashtagsView, 
    TweetsView,
    LatestTweetView,
    TweetDetailView,
    ValidSendersView
)

urlpatterns = [
    path('popularity/', PopularityScoreView.as_view(), name='popularity-score'),
    path('safety/', SafetyScoreView.as_view(), name='safety-score'),
    path('compare_hashtags/', CompareHashtagsView.as_view(), name='compare-hashtags'),
    path('tweets/', TweetsView.as_view(), name='tweets'),
    path('tweets/latest/', LatestTweetView.as_view(), name='latest-tweet'),
    path('tweets/senders/', ValidSendersView.as_view(), name='valid-senders'),
    path('tweets/<str:tweet_id>/', TweetDetailView.as_view(), name='tweet-detail'),
]