from django.urls import path
from . import views

urlpatterns = [
    path('assign_reviewer_to_paper/', views.assign_reviewer_to_paper, name='assign_reviewer_to_paper'),
    path('remove_reviewer_from_paper/', views.remove_reviewer_from_paper, name='remove_reviewer_from_paper'),
]