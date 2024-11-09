import json
from django.urls import reverse
from django.utils import timezone
from django.test import TestCase, Client
from rest_framework.test import APITestCase

from .models import User, Conference
from conference_roles.models import ConferenceRole

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
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json()["detail"], "Method \"GET\" not allowed.")


class DeleteConferenceTestCase(TestCase):
    def setUp(self):
        # Crea un utente
        self.user = User.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password="password"
        )

        # Crea una conferenza
        self.conference = Conference.objects.create(
            title="Test Conference",
            admin_id=self.user,
            deadline="2023-12-31 23:59:59",
            description="This is a test conference"
        )

        # Crea un ruolo di conferenza per l'utente
        self.conference_role = ConferenceRole.objects.create(
            user=self.user,
            conference=self.conference,
            role="admin"
        )

        self.client = Client()

    def test_delete_conference_as_admin(self):
        # Effettua il login dell'utente
        self.client.force_login(self.user)

        # Invia la richiesta per eliminare la conferenza
        response = self.client.post(
            reverse('delete_conference'),
            data={'conference_id': self.conference.id, 'user_id': self.user.id},
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'message': 'Conference deleted successfully'})

        # Verifica che la conferenza sia stata eliminata
        self.assertFalse(Conference.objects.filter(id=self.conference.id).exists())

    def test_delete_conference_without_permission(self):
        # Crea un nuovo utente
        other_user = User.objects.create(
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            password="password"
        )

        # Effettua il login dell'altro utente
        self.client.force_login(other_user)

        # Invia la richiesta per eliminare la conferenza
        response = self.client.post(
            reverse('delete_conference'),
            data={'conference_id': self.conference.id, 'user_id': other_user.id},
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {'error': 'Permission denied. User is not an admin of this conference.'})

        # Verifica che la conferenza non sia stata eliminata
        self.assertTrue(Conference.objects.filter(id=self.conference.id).exists())

    def test_delete_conference_with_missing_fields(self):
        # Effettua il login dell'utente
        self.client.force_login(self.user)

        # Invia la richiesta senza i campi obbligatori
        response = self.client.post(
            reverse('delete_conference'),
            data={},
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'Missing conference_id'})

        # Verifica che la conferenza non sia stata eliminata
        self.assertTrue(Conference.objects.filter(id=self.conference.id).exists())

    def test_delete_conference_with_invalid_json(self):
        # Effettua il login dell'utente
        self.client.force_login(self.user)

        # Invia la richiesta con un JSON non valido
        response = self.client.post(
            reverse('delete_conference'),
            data='invalid json',
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'Invalid JSON'})

        # Verifica che la conferenza non sia stata eliminata
        self.assertTrue(Conference.objects.filter(id=self.conference.id).exists())

    def test_delete_conference_with_non_existent_conference(self):
        # Effettua il login dell'utente
        self.client.force_login(self.user)

        # Invia la richiesta per eliminare una conferenza inesistente
        response = self.client.post(
            reverse('delete_conference'),
            data={'conference_id': 999, 'user_id': self.user.id},
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'error': 'Conference not found'})

        # Verifica che la conferenza non sia stata eliminata
        self.assertTrue(Conference.objects.filter(id=self.conference.id).exists())


# -------------------------------------------------------------------------------------------------------------------------------------- #
#                       tests for edit_conference:
