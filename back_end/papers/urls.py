from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_paper, name='create_paper'),
    path('list/', views.list_papers, name='list_papers'),
]