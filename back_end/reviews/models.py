from django.db import models
from papers.models import Paper  # Assicurati che l'import sia corretto
from users.models import User

class Review(models.Model):
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    comment_text = models.TextField()
    score = models.IntegerField()
    confidence_level = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.paper.title} by {self.user.first_name} {self.user.last_name} - Score: {self.score}"
    
    
