from django.db import models
from conference.models import Conference
from users.models import User

class Paper(models.Model):
    STATUS = [
        ('submitted', 'Submitted'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    ]

    title = models.CharField(max_length=200)
    paper_file = models.FileField(upload_to='papers_pdf/', null=True, blank=True)
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name="papers")
    author_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name="papers")
    status_id = models.CharField(max_length=20, choices=STATUS)

    def str(self):
        return f"{self.title} - {self.author} - {self.conference.title} ({self.status})"