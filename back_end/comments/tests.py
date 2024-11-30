from django.utils import timezone
from django.test import TestCase
from django.urls import reverse
import json

from users.models import User
from reviews.models import Review
from .models import Comment
from papers.models import Paper
from conference.models import Conference


class CommentTests(TestCase):
    def setUp(self):
        # Create users
        self.user = User.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password="password"
        )
        self.admin_user = User.objects.create(
            first_name="Admin",
            last_name="User",
            email="admin@example.com",
            password="securepassword"
        )

        # Create conference
        self.conference = Conference.objects.create(
            title="Test Conference",
            admin_id=self.admin_user,
            deadline=timezone.now() + timezone.timedelta(days=7),
            description="Conference description"
        )

        # Create paper
        self.paper = Paper.objects.create(
            title="Test Paper",
            conference=self.conference,
            author_id=self.user,
            status_id='submitted'
        )

        # Create review
        self.review = Review.objects.create(
            paper=self.paper,
            user=self.admin_user,
            comment_text="Initial review",
            score=8
        )

        # Set up URLs
        self.url_create_comment = reverse('create_comment')
        self.url_get_comments = reverse('get_all_comments')


    def test_add_comment_missing_fields(self):
        """Test adding a comment with missing fields"""
        self.client.force_login(self.user)

        payload = {"id_review": self.review.id}  # No text
        response = self.client.post(
            self.url_create_comment,
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Missing fields")

    def test_add_comment_invalid_review(self):
        """Test adding a comment to a non-existent review"""
        self.client.force_login(self.user)

        payload = {
            "id_review": 9999,  # Non-existent ID
            "text": "Commento non valido"
        }
        response = self.client.post(
            self.url_create_comment,
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "Review not found")

    def test_get_comments_successful(self):
        """Test retrieving comments for a review"""
        # Create comments for the review
        Comment.objects.create(
            user=self.user,
            review=self.review,
            comment_text="Primo commento"
        )
        Comment.objects.create(
            user=self.admin_user,
            review=self.review,
            comment_text="Secondo commento"
        )

        response = self.client.get(self.url_get_comments)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(isinstance(response_data, list))
        self.assertEqual(len(response_data), 2)

        comments_text = [comment["comment_text"] for comment in response_data]
        self.assertIn("Primo commento", comments_text)
        self.assertIn("Secondo commento", comments_text)