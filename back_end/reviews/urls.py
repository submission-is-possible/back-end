from django.urls import path
from . import views

urlpatterns = [
    path('user_reviews/', views.get_user_reviews, name='get_user_reviews'),
]