import json
from django.urls import reverse
from django.utils import timezone
from django.test import TestCase
from .models import User, Conference

class ConferenceCreationTests(TestCase):
    def setUp(self):
        # Crea un utente amministratore per i test
        self.admin_user = User.objects.create(
            first_name="Admin",
            last_name="User",
            email="admin@example.com",
            password="securepassword"
        )
        self.url = reverse('create_conference')  # Assicurati che l'URL corrisponda al nome dato nella tua configurazione degli URL

    def test_create_conference_successful(self):
        """Test per la creazione di una conferenza con dati validi"""
        payload = {
            "title": "Test Conference",
            "admin_id": self.admin_user.id,
            "deadline": (timezone.now() + timezone.timedelta(days=7)).isoformat(),
            "description": "Description of the test conference"
        }
        response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["message"], "Conference created successfully")
        self.assertIn("conference_id", response.json())
        # Verifica che la conferenza sia stata creata nel database
        conference = Conference.objects.get(id=response.json()["conference_id"])
        self.assertEqual(conference.title, payload["title"])
        self.assertEqual(conference.admin_id, self.admin_user)

    def test_create_conference_missing_fields(self):
        """Test per mancanza di campi obbligatori"""
        payload = {
            "title": "Test Conference",
            "admin_id": self.admin_user.id,
            # Campo "deadline" e "description" mancante
        }
        response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Missing fields")

    def test_create_conference_invalid_admin(self):
        """Test per ID admin non valido"""
        payload = {
            "title": "Test Conference",
            "admin_id": 9999,  # Un ID che non esiste
            "deadline": (timezone.now() + timezone.timedelta(days=7)).isoformat(),
            "description": "Description of the test conference"
        }
        response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "Admin user not found")

    def test_create_conference_invalid_json(self):
        """Test per dati JSON non validi"""
        invalid_json_payload = "This is not JSON"
        response = self.client.post(self.url, data=invalid_json_payload, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Invalid JSON")

    def test_create_conference_invalid_method(self):
        """Test per metodo di richiesta non valido (non POST)"""
        response = self.client.get(self.url)  # Invio una richiesta GET
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json()["error"], "Only POST requests are allowed")


class ConferenceDeletionTests(TestCase):

    def setUp(self):
        # Crea un utente amministratore e una conferenza per i test
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
            description="Test description"
        )
        self.url = reverse('delete_conference')  # Assicurati che il nome corrisponda all'URL configurato

    def test_delete_conference_successful(self):
        """Test per eliminare una conferenza con successo"""
        payload = {
            "conference_id": self.conference.id,
        }
        response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Conference deleted successfully")
        
        # Verifica che la conferenza non esista più nel database
        with self.assertRaises(Conference.DoesNotExist):
            Conference.objects.get(id=self.conference.id)

    def test_delete_conference_not_found(self):
        """Test per tentare di eliminare una conferenza che non esiste"""
        payload = {
            "conference_id": 9999,  # ID di una conferenza inesistente
        }
        response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "Conference not found")

    def test_delete_conference_missing_id(self):
        """Test per tentare di eliminare una conferenza senza specificare l'ID"""
        payload = {
            # Campo "conference_id" mancante
        }
        response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Missing conference_id")

    def test_delete_conference_invalid_json(self):
        """Test per tentare di eliminare una conferenza con dati JSON non validi"""
        invalid_json_payload = "This is not JSON"
        response = self.client.post(self.url, data=invalid_json_payload, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Invalid JSON")

    def test_delete_conference_invalid_method(self):
        """Test per tentare di eliminare una conferenza con un metodo diverso da POST"""
        response = self.client.get(self.url)  # Invio una richiesta GET
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json()["error"], "Only POST requests are allowed")