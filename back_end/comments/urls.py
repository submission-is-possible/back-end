from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_comment, name='create_comment'),
    path('allthecomments/list/', views.get_all_comments, name='get_all_comments'),
    path('<int:comment_id>/', views.get_comment_by_id, name='get_specific_comment'),
    path('<int:comment_id>/update/', views.update_comment, name='update_comment'),
    path('paper/<int:paper_id>/get_comments', views.get_comments_by_paper, name='get_comments_by_paper'),
    path('delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('deleteall/paper/<int:paper_id>', views.delete_comments_by_paper, name='delete_all_comments_of_paper'),
    path('deleteall/review/<int:review_id>', views.delete_comments_by_review, name='delete_all_comments_of_review'),
    path('deleteall/user/<int:user_id>', views.delete_comments_by_user, name='delete_all_comments_of_user'),
]