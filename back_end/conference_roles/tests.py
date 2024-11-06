import json
from django.urls import reverse
from django.test import TestCase, Client, RequestFactory
from django.utils import timezone
from .models import User, Conference, ConferenceRole
from django.contrib.auth.hashers import make_password

class ConferenceRoleCreationTests(TestCase):
    def setUp(self):
        # Crea un utente e una conferenza per i test
        self.user = User.objects.create(
            first_name="Mario",
            last_name="Rossi",
            email="mario.rossi@example.com",
            password="password123"
        )
        self.conference = Conference.objects.create(
            title="AI Conference",
            admin_id=self.user,
            deadline=timezone.now() + timezone.timedelta(days=30),
            description="A conference on AI advancements."
        )
        self.url = reverse('create_conference_role')  # Assicurati che l'URL corrisponda al nome dato nella configurazione degli URL

    def test_create_conference_role_successful(self):
        """Test per la creazione di un ruolo di conferenza con dati validi"""
        payload = {
            "id_user": self.user.id,
            "id_conference": self.conference.id,
            "role_user": "reviewer"
        }
        response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["message"], "Role added successfully")
        
        # Verifica che il ruolo sia stato creato nel database
        self.assertTrue(ConferenceRole.objects.filter(user=self.user, conference=self.conference, role="reviewer").exists())

    def test_create_conference_role_missing_fields(self):
        """Test per mancanza di campi obbligatori"""
        payload = {
            "id_conference": self.conference.id,
            "role_user": "author"  # Manca id_user
        }
        response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Missing fields")

    def test_create_conference_role_user_not_found(self):
        """Test per ID utente non valido"""
        payload = {
            "id_user": 9999,  # ID utente non esistente
            "id_conference": self.conference.id,
            "role_user": "admin"
        }
        response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "User not found")

    def test_create_conference_role_conference_not_found(self):
        """Test per ID conferenza non valido"""
        payload = {
            "id_user": self.user.id,
            "id_conference": 9999,  # ID conferenza non esistente
            "role_user": "author"
        }
        response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "Conference not found")

    def test_create_conference_role_invalid_role(self):
        """Test per ruolo utente non valido"""
        payload = {
            "id_user": self.user.id,
            "id_conference": self.conference.id,
            "role_user": "invalid_role"  # Ruolo non valido
        }
        response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Invalid role")

    def test_create_conference_role_invalid_json(self):
        """Test per dati JSON non validi"""
        invalid_json_payload = "This is not JSON"
        response = self.client.post(self.url, data=invalid_json_payload, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Invalid JSON")

    def test_create_conference_role_invalid_method(self):
        """Test per metodo di richiesta non valido (non POST)"""
        response = self.client.get(self.url)  # Invio una richiesta GET
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json()["error"], "Only POST requests are allowed")

class GetUserConferencesTests(TestCase):
    def setUp(self):
        # Crea un utente e alcune conferenze per i test
        self.user = User.objects.create(
            first_name="Mario",
            last_name="Rossi",
            email="mariorossi@gmail.com",
            password="password123"
        )
        self.conference1 = Conference.objects.create(
            title="AI Conference",
            admin_id=self.user,
            deadline=timezone.now() + timezone.timedelta(days=30),
            description="A conference on AI advancements."
        )
        self.conference2 = Conference.objects.create(
            title="Tech Summit",
            admin_id=self.user,
            deadline=timezone.now() + timezone.timedelta(days=60),
            description="An annual tech summit."
        )
         # Associa le conferenze all'utente tramite 'conference_roles'
        ConferenceRole.objects.create(user=self.user, conference=self.conference1)
        ConferenceRole.objects.create(user=self.user, conference=self.conference2)
        self.url = reverse('get_user_conferences')

    def test_get_user_conferences_successful(self):
        """Test per ottenere conferenze di un utente con paginazione"""
        payload = {
            "user_id": self.user.id
        }
        response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_conferences"], 2)  # L'utente ha 2 conferenze

    def test_get_user_conferences_missing_user_id(self):
        """Test per mancanza di user_id"""
        payload = {}  # Mancante user_id
        response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Missing user_id")

    def test_get_user_conferences_invalid_json(self):
        """Test per dati JSON non validi"""
        invalid_json_payload = "This is not JSON"
        response = self.client.post(self.url, data=invalid_json_payload, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Invalid JSON")

    def test_get_user_conferences_invalid_method(self):
        """Test per metodo di richiesta non valido (non POST)"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json()["error"], "Only POST requests are allowed")