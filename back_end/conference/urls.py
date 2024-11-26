from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_conference, name='create_conference'),
    path('delete/', views.delete_conference, name='delete_conference'),
    path('edit/', views.edit_conference, name='edit_conference'),
    path('upload_reviewers_csv/', views.upload_reviewers_csv, name='upload_reviewers_csv'),
    path('list/', views.get_conferences, name='get_conferences'),
    
    path('get_conference_papers_by_user_role/', views.get_conference_papers_by_user_role, name='get_conference_papers_by_user_role'),
]