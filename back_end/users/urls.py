from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_user, name='create_user'),
    path('login/', views.login_user, name='login'),
    path('list/', views.list_users, name='list_users'),
]