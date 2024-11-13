from django.urls import path
from . import views

urlpatterns = [
    path('get_user_reviews/', views.get_user_reviews, name='get_user_reviews'),
    path('get_paper_reviews/', views.get_paper_reviews, name='get_paper_reviews'),
]