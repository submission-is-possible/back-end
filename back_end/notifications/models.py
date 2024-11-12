from django.db import models
from users.models import User
from conference.models import Conference

class Notification(models.Model):
    STATUS_CHOICES = [
        (-1, 'rejected'),
        (0, 'pending'),
        (1, 'accepted'),
    ]

    TYPE_CHOICES = [
        (0, 'author'),
        (1, 'reviewer'),
    ]

    user_sender = models.ForeignKey(User, related_name='sent_notifications', on_delete=models.CASCADE)
    user_receiver = models.ForeignKey(User, related_name='received_notifications', on_delete=models.CASCADE)
    conference = models.ForeignKey(Conference, related_name='notifications', on_delete=models.CASCADE)
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)
    type = models.IntegerField(choices=TYPE_CHOICES, default=0)

    def __str__(self):
        return f"Notification from {self.user_sender} to {self.user_receiver} - {self.get_status_display()}"
