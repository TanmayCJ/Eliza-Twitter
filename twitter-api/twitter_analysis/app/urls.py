from django.urls import path
from .views import TwitterAnalysisView, TwitterDisplayView

urlpatterns = [
    path('analyze/', TwitterAnalysisView.as_view(), name='twitter-analysis'),
    path('display/', TwitterDisplayView.as_view(), name='twitter-display')
]
