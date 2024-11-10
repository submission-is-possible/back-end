from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_conference, name='create_conference'),
    path('delete/', views.delete_conference, name='delete_conference'),
    path('edit/', views.edit_conference, name='edit_conference'),
]