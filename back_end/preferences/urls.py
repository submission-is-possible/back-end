from django.urls import path
from . import views

urlpatterns = [

    path('save/', views.save_preferences, name = 'save_preferences'),
    #path('get_user_preferences/', views.get_preferences, name = 'get_preferences'),
    path('add_preference/', views.add_preference, name = 'add_preference'),
    path('get_preference_papers_in_conference_by_reviewer/', views.get_preference_papers_in_conference_by_reviewer, name = 'get_preference_papers_in_conference_by_reviewer'),
]