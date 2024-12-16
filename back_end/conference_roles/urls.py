from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_conference_role, name='create_conference_role'),
    # per mappare la vista `get_user_conferences` a un URL
    path('get_user_conferences/', views.get_user_conferences, name='get_user_conferences'),
    path('assign_author_role/', views.assign_author_role, name='assign_author_role'),

]