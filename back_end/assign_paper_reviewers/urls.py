from django.urls import path
from . import views

urlpatterns = [
    path('assign_reviewer_to_paper/', views.assign_reviewer_to_paper, name='assign_reviewer_to_paper'),
]