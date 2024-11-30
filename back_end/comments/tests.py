import json
from django.utils import timezone

from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APITestCase
from .models import User, Comment
from conference.models import Conference


class CommentTests(TestCase):
    def setUp(self):
        # Creazione di utenti e conferenza per i test
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
        self.conference = Conference.objects.create(
            title="Test Conference",
            admin_id=self.admin_user,
            deadline=timezone.now() + timezone.timedelta(days=7),
            description="Conference description"
        )
        self.url_add_comment = reverse('add_comment')
        self.url_get_comments = reverse('get_comments')

    def test_add_comment_successful(self):
        """Test per aggiungere un commento con dati validi"""
        self.client.force_login(self.user)
        session = self.client.session
        session['_auth_user_id'] = self.user.id
        session.save()

        payload = {
            "conference_id": self.conference.id,
            "content": "Questo è un commento di prova"
        }
        response = self.client.post(
            self.url_add_comment,
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        response_data = response.json()
        self.assertIn("message", response_data)
        self.assertEqual(response_data["message"], "Comment added successfully")

        comment = Comment.objects.get(id=response_data["comment_id"])
        self.assertEqual(comment.content, payload["content"])
        self.assertEqual(comment.conference.id, self.conference.id)
        self.assertEqual(comment.user.id, self.user.id)

    def test_add_comment_missing_fields(self):
        """Test per l'aggiunta di un commento con campi mancanti"""
        self.client.force_login(self.user)
        session = self.client.session
        session['_auth_user_id'] = self.user.id
        session.save()

        payload = {"conference_id": self.conference.id}  # Nessun contenuto
        response = self.client.post(
            self.url_add_comment,
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Missing required fields")

    def test_add_comment_invalid_conference(self):
        """Test per l'aggiunta di un commento a una conferenza non esistente"""
        self.client.force_login(self.user)
        session = self.client.session
        session['_auth_user_id'] = self.user.id
        session.save()

        payload = {
            "conference_id": 9999,  # ID inesistente
            "content": "Commento non valido"
        }
        response = self.client.post(
            self.url_add_comment,
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "Conference not found")

    def test_get_comments_successful(self):
        """Test per ottenere i commenti di una conferenza"""
        # Creazione di commenti per la conferenza
        Comment.objects.create(
            user=self.user,
            conference=self.conference,
            content="Primo commento"
        )
        Comment.objects.create(
            user=self.admin_user,
            conference=self.conference,
            content="Secondo commento"
        )

        response = self.client.get(self.url_get_comments + f"?conference_id={self.conference.id}")
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("comments", response_data)
        self.assertEqual(len(response_data["comments"]), 2)

        comments_content = [comment["content"] for comment in response_data["comments"]]
        self.assertIn("Primo commento", comments_content)
        self.assertIn("Secondo commento", comments_content)

    def test_get_comments_invalid_conference(self):
        """Test per ottenere commenti di una conferenza non esistente"""
        response = self.client.get(self.url_get_comments + "?conference_id=9999")  # ID inesistente
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "Conference not found")
