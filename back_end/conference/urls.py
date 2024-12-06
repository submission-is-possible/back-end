from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_conference, name='create_conference'),
    path('delete/', views.delete_conference, name='delete_conference'),
    path('edit/', views.edit_conference, name='edit_conference'),
    path('upload_reviewers_csv/', views.upload_reviewers_csv, name='upload_reviewers_csv'),
    path('list/', views.get_conferences, name='get_conferences'),
    
    path('get_paper_inconference_reviewer/', views.get_paper_inconference_reviewer, name='get_paper_inconference_reviewer'),
    path('get_paper_inconference_author/', views.get_paper_inconference_author, name='get_paper_inconference_author'),
    path('get_paper_inconference_admin/', views.get_paper_inconference_admin, name='get_paper_inconference_admin'),
    path('automatic_assign_reviewers/', views.automatic_assign_reviewers, name='automatic_assign_reviewers'),
    path('get_automatic_assign_status/', views.get_automatic_assign_status, name='get_automatic_assign_status'),

    path('get_all_papers/<int:conference_id>/', views.get_all_papers, name='get_all_papers'),
]