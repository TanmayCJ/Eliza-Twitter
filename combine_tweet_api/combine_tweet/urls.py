from django.urls import path
from combine_tweet import views

urlpatterns = [
    path('', views.home, name='home'),
    path('latest-entry/', views.latest_entry, name='latest-entry'),
    path('generate-combined/', views.generate_combined, name='generate-combined'),
    path('test/', views.test, name='test'),
    path('test-with-sample/', views.test_with_sample, name='test-with-sample'),
    path('generate-branded/', views.generate_branded_tweet, name='generate-branded'),
    path('generate-branded-latest/', views.generate_branded_from_latest, name='generate-branded-latest'),
    path('api/branded_tweet/', views.generate_branded_tweet, name='generate_branded_tweet'),
    path('generate-forced-branded-latest/', views.generate_forced_branded_from_latest, name='generate-forced-branded-latest'),
    path('generate_combined_post/', views.generate_combined_post, name='generate_combined_post'),
]
