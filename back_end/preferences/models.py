from django.db import models
from users.models import User  
from papers.models import Paper

class Preference(models.Model):
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name="preferences")
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="preferences")
    preference = models.IntegerField()

    def __str__(self):
        return f"preference for {self.paper} of {self.reviewer} score is: {self.preference})"