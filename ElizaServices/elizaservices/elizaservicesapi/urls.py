from django.urls import path
from .views import (
    PopularityScoreView,
    CompareHashtagsView,
    SafetyScoreView, 
    TweetsView,
    LatestTweetView,
    SingleTweetView,
    ValidSendersView,
    TwitterTrendsView,
    TwitterTimeframesView
)

urlpatterns = [
    path('popularity/', PopularityScoreView.as_view(), name='popularity-score'),
    path('compare_hashtags/', CompareHashtagsView.as_view(), name='compare-hashtags'),
    path('safety/', SafetyScoreView.as_view(), name='safety-score'),
    path('tweets/', TweetsView.as_view(), name='tweets'),
    path('tweets/latest/', LatestTweetView.as_view(), name='latest-tweet'),
    path('tweets/senders/', ValidSendersView.as_view(), name='valid-senders'),
    path('tweets/<str:tweet_id>/', SingleTweetView.as_view(), name='tweet-detail'),
    path('twitter/trends/', TwitterTrendsView.as_view(), name='twitter-trends'),
    path('twitter/timeframes/', TwitterTimeframesView.as_view(), name='twitter-timeframes'),
]