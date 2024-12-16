from django.urls import path
from .views import *

urlpatterns = [
    path('get-notifications-received/', get_notifications_received, name='get_notifications_received'),
    path('create-notification/', create_notification, name='create_notification'),
    path('delete-notification/', delete_notification, name='delete_notification'),
    path('update-notification/', update_notification, name='update_notification'),

]
