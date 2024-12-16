from django.db import models
from users.models import User  
from papers.models import Paper

class Preference(models.Model):
    PREFERENCE_CHOICES = [
        ('not_interested', 'Not Interested'),
        ('interested', 'Interested')
    ]
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name="preferences")
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="preferences")
    # not interested, interested
    preference = models.CharField(max_length=20, choices=PREFERENCE_CHOICES)

    def __str__(self):
        return f"preference for {self.paper} of {self.reviewer} score is: {self.preference})"