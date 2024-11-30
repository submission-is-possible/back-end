from django.urls import path
from . import views

urlpatterns = [
    path('assign_reviewer_to_paper/', views.assign_reviewer_to_paper, name='assign_reviewer_to_paper'),
    path('remove_reviewer_from_paper/', views.remove_reviewer_from_paper, name='remove_reviewer_from_paper'),

    path('get_reviewers_for_paper/', views.get_all_reviewers_assigned_to_paper_for_conference, name='get_reviewers_for_paper'),
]