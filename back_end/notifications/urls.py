from django.urls import path
from . import views

urlpatterns = [
    path('notifications/create/', views.create_notification, name='create_notification'),
    path('notifications/get/', views.get_notifications, name='get_notifications'),
    path('notifications/mark-read/', views.mark_as_read, name='mark_as_read'),
    path('notifications/delete/', views.delete_notification, name='delete_notification'),
]
