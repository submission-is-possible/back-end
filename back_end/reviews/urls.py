from django.urls import path
from . import views

urlpatterns = [
    path('get_user_reviews/', views.get_user_reviews, name='get_user_reviews'),
    path('get_paper_reviews/', views.get_paper_reviews, name='get_paper_reviews'),

    path('create_review/', views.create_review, name='create_review'),
    path('update_review/<int:review_id>/', views.update_review, name='update_review'),
    path('delete_review/<int:review_id>/', views.delete_review, name='delete_review'),
]