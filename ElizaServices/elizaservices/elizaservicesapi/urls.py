from django.urls import path
from .views import (
    PopularityScoreView,
    CompareHashtagsView,
    SafetyScoreView, 
    TweetsView,
    LatestTweetView,
    ValidSendersView,
    EnvironmentalNewsView,
    ImageGenView,
    QueuedTweetView,
    LatestNTweetsView,  # added import
)

urlpatterns = [
    path('popularity/', PopularityScoreView.as_view(), name='popularity-score'),
    path('safety/', SafetyScoreView.as_view(), name='safety-score'),
    path('compare_hashtags/', CompareHashtagsView.as_view(), name='compare-hashtags'),

    path('tweets/', TweetsView.as_view(), name='tweets'),
    path('tweets/latest/', LatestTweetView.as_view(), name='latest-tweet'),
    path('tweets/senders/', ValidSendersView.as_view(), name='valid-senders'),
    path('tweets/latest_n/', LatestNTweetsView.as_view(), name='latest-n-tweets'),

    path('news/', EnvironmentalNewsView.as_view(), name='environmental-news'),

    path('imagegen/', ImageGenView.as_view(), name='imagegen'),

    path('queuedtweets/', QueuedTweetView.as_view(), name='queued-tweet-detail')
]