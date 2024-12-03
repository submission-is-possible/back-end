from django.urls import path
from . import views

urlpatterns = [

    path('save/', views.save_preferences, name = 'save_preferences'),
    #path('get_user_preferences/', views.get_preferences, name = 'get_preferences')
]