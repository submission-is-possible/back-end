from django.db import models
from papers.models import Paper
from users.models import User
from conference.models import Conference

class PaperReviewAssignment(models.Model):
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
    ]

    paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name="review_assignments")
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assigned_papers")
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name="review_assignments")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')
    #assigned_at = models.DateTimeField(auto_now_add=True)
    #updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Reviewer: {self.reviewer.email} - Paper: {self.paper.title} - Status: {self.status}"
