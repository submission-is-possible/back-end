from django.db import models
from papers.models import Paper  # Assicurati che l'import sia corretto
from users.models import User
from conference.models import Conference

class Review(models.Model):
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    comment_text = models.TextField()
    score = models.IntegerField()
    confidence_level = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.paper.title} by {self.user.first_name} {self.user.last_name} - Score: {self.score}"
    
    
class ReviewTemplateItem(models.Model):
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name="templateItem")
    label = models.TextField()
    description = models.TextField()
    has_comment = models.BooleanField()
    has_score = models.BooleanField()


class ReviewItem(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="reviewsItem")
    templateItem = models.ForeignKey(ReviewTemplateItem, on_delete=models.CASCADE, related_name="reviewsItem")
    comment = models.TextField()
    score = models.IntegerField()