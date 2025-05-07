from django.urls import path
from .views import (
    PopularityScoreView,
    CompareHashtagsView,
    SafetyScoreView, 
    TweetsView,
    LatestTweetView,
    SingleTweetView,
    ValidSendersView,
<<<<<<< HEAD
    TwitterTrendsView,
    TwitterTimeframesView
=======
    EnvironmentalNewsView,
    ImageGenView,
    TextEmotionView
>>>>>>> 1207268b3aa5a6d6a44afa8286eaed28487576df
)

urlpatterns = [
    path('popularity/', PopularityScoreView.as_view(), name='popularity-score'),
    path('compare_hashtags/', CompareHashtagsView.as_view(), name='compare-hashtags'),
    path('safety/', SafetyScoreView.as_view(), name='safety-score'),
    path('tweets/', TweetsView.as_view(), name='tweets'),
    path('tweets/latest/', LatestTweetView.as_view(), name='latest-tweet'),
    path('tweets/senders/', ValidSendersView.as_view(), name='valid-senders'),
    path('tweets/<str:tweet_id>/', SingleTweetView.as_view(), name='tweet-detail'),
<<<<<<< HEAD
    path('twitter/trends/', TwitterTrendsView.as_view(), name='twitter-trends'),
    path('twitter/timeframes/', TwitterTimeframesView.as_view(), name='twitter-timeframes'),
=======
    path('news/', EnvironmentalNewsView.as_view(), name='environmental-news'),
    path('imagegen/', ImageGenView.as_view(), name='imagegen'),
    path('text-emotion/', TextEmotionView.as_view(), name='text-emotion'),
>>>>>>> 1207268b3aa5a6d6a44afa8286eaed28487576df
]