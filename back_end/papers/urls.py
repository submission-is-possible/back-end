from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_paper, name='create_paper'),
    path('list/', views.list_papers, name='list_papers'),
    path('conf_list/', views.list_conf_papers,  name='list_conf_papers'),
    path('paper/<str:filename>/', views.view_paper_pdf, name='view_paper_pdf'),

path('update_status/', views.update_paper_status, name='update_paper_status'),
]
