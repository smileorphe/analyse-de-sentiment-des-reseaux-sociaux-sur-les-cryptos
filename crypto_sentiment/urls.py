from django.urls import path
from . import views

app_name = 'crypto_sentiment'

urlpatterns = [
    path('', views.landing, name='landing'),  # Nouvelle landing page
    path('dashboard/', views.dashboard, name='dashboard'),
    path('analysis/', views.analysis, name='analysis'),
    path('posts/', views.posts_list, name='posts_list'),
    path('trigger-scraping/', views.trigger_scraping, name='trigger_scraping'),
]