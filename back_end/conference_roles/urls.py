from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_conference_role, name='create_conference_role'),
    # per mappare la vista `get_user_conferences` a un URL
    path('user/<int:user_id>/conferences/', views.get_user_conferences, name='get_user_conferences'),
]