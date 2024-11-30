
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from comments.models import Comment
from reviews.models import Review
from papers.models import Paper

User = get_user_model()


class CommentAPITestCase(APITestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="password123"
        )

        # Authenticate the client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create a test paper
        self.paper = Paper.objects.create(title="Test Paper", content="Paper content here")

        # Create a test review for the paper
        self.review = Review.objects.create(paper=self.paper, user=self.user, content="This is a test review")

        # URL endpoints
        self.create_comment_url = "/api/comments/"
        self.get_all_comments_url = "/api/comments/"
        self.get_comment_by_id_url = lambda comment_id: f"/api/comments/{comment_id}/"
        self.update_comment_url = lambda comment_id: f"/api/comments/{comment_id}/"
        self.delete_comment_url = lambda comment_id: f"/api/comments/{comment_id}/"
        self.delete_comments_by_paper_url = f"/api/papers/{self.paper.id}/comments/"
        self.delete_comments_by_user_url = f"/api/users/{self.user.id}/comments/"
        self.delete_comments_by_review_url = f"/api/reviews/{self.review.id}/comments/"

    def test_create_comment(self):
        data = {
            "id_review": self.review.id,
            "text": "This is a test comment"
        }
        response = self.client.post(self.create_comment_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(Comment.objects.first().comment_text, data["text"])

    def test_get_all_comments(self):
        Comment.objects.create(user=self.user, review=self.review, comment_text="First comment")
        Comment.objects.create(user=self.user, review=self.review, comment_text="Second comment")
        response = self.client.get(self.get_all_comments_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_comment_by_id(self):
        comment = Comment.objects.create(user=self.user, review=self.review, comment_text="Single comment")
        response = self.client.get(self.get_comment_by_id_url(comment.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["comment_text"], comment.comment_text)

    def test_update_comment(self):
        comment = Comment.objects.create(user=self.user, review=self.review, comment_text="Old comment")
        data = {"comment_text": "Updated comment"}
        response = self.client.patch(self.update_comment_url(comment.id), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        comment.refresh_from_db()
        self.assertEqual(comment.comment_text, data["comment_text"])

    def test_delete_comment(self):
        comment = Comment.objects.create(user=self.user, review=self.review, comment_text="To be deleted")
        response = self.client.delete(self.delete_comment_url(comment.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Comment.objects.count(), 0)

    def test_delete_comments_by_paper(self):
        Comment.objects.create(user=self.user, review=self.review, comment_text="Comment 1")
        Comment.objects.create(user=self.user, review=self.review, comment_text="Comment 2")
        response = self.client.delete(self.delete_comments_by_paper_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Comment.objects.count(), 0)

    def test_delete_comments_by_user(self):
        Comment.objects.create(user=self.user, review=self.review, comment_text="User comment")
        response = self.client.delete(self.delete_comments_by_user_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Comment.objects.count(), 0)

    def test_delete_comments_by_review(self):
        Comment.objects.create(user=self.user, review=self.review, comment_text="Comment 1")
        Comment.objects.create(user=self.user, review=self.review, comment_text="Comment 2")
        response = self.client.delete(self.delete_comments_by_review_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Comment.objects.count(), 0)
