import json
from django.urls import reverse
from django.test import TestCase
from django.utils import timezone
from .models import User, Conference, ConferenceRole

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
        # Crea un utente per i test
        self.user = User.objects.create(
            first_name="Mario",
            last_name="Rossi",
            email="mario.rossi@example.com",
            password="password123"
        )

        # Crea alcune conferenze
        self.conference1 = Conference.objects.create(
            title="AI Conference 1",
            admin_id=self.user,
            deadline=timezone.now() + timezone.timedelta(days=30),
            description="A conference on AI advancements 1."
        )
        self.conference2 = Conference.objects.create(
            title="AI Conference 2",
            admin_id=self.user,
            deadline=timezone.now() + timezone.timedelta(days=30),
            description="A conference on AI advancements 2."
        )
        self.conference3 = Conference.objects.create(
            title="AI Conference 3",
            admin_id=self.user,
            deadline=timezone.now() + timezone.timedelta(days=30),
            description="A conference on AI advancements 3."
        )

        # Associa l'utente alle conferenze tramite ConferenceRole
        ConferenceRole.objects.create(user=self.user, conference=self.conference1, role='reviewer')
        ConferenceRole.objects.create(user=self.user, conference=self.conference2, role='admin')
        ConferenceRole.objects.create(user=self.user, conference=self.conference3, role='author')

        # URL per la richiesta GET
        self.url = reverse('get_user_conferences', args=[self.user.id])

    def test_get_user_conferences_default_page(self):
        """Test che verifica se la risposta contiene le conferenze corrette con paginazione predefinita."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(response_data['current_page'], 1)
        self.assertEqual(response_data['total_pages'], 1)
        self.assertEqual(response_data['total_conferences'], 3)

        # Verifica che le conferenze siano incluse nella risposta
        self.assertEqual(len(response_data['conferences']), 3)
        self.assertEqual(response_data['conferences'][0]['title'], 'AI Conference 1')
        self.assertEqual(response_data['conferences'][1]['title'], 'AI Conference 2')
        self.assertEqual(response_data['conferences'][2]['title'], 'AI Conference 3')

    def test_get_user_conferences_no_conferences(self):
        """Test che verifica la risposta quando l'utente non ha conferenze associate."""
        new_user = User.objects.create(
            first_name="Giovanni",
            last_name="Verdi",
            email="giovanni.verdi@example.com",
            password="password456"
        )
        url_no_conferences = reverse('get_user_conferences', args=[new_user.id])

        response = self.client.get(url_no_conferences)
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(response_data['current_page'], 1)
        self.assertEqual(response_data['total_pages'], 1)
        self.assertEqual(response_data['total_conferences'], 0)
        self.assertEqual(len(response_data['conferences']), 0)