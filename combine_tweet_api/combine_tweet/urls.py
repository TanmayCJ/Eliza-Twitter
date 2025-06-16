from django.urls import path
from combine_tweet import views

urlpatterns = [
    path('', views.home, name='home'),
    path('latest-entry/', views.latest_entry, name='latest-entry'),
    path('generate-combined/', views.generate_combined, name='generate-combined'),
    path('test/', views.test, name='test'),
    path('test-with-sample/', views.test_with_sample, name='test-with-sample'),
    path('generate-combined-post/', views.generate_combined_post, name='generate_combined_post'),
]
