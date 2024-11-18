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

        self.client.force_login(self.admin_user)

        session = self.client.session
        session['_auth_user_id'] = self.admin_user.id
        session.save()

        payload = {
            "title": "Test Conference",
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

        self.client.force_login(self.admin_user)

        session = self.client.session
        session['_auth_user_id'] = self.admin_user.id
        session.save()

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

        self.client.force_login(self.admin_user)

        session = self.client.session
        session['_auth_user_id'] = 9999
        session.save()

        payload = {
            "title": "Test Conference",
            "deadline": (timezone.now() + timezone.timedelta(days=7)).isoformat(),
            "description": "Description of the test conference"
        }
        response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "User not found")

    def test_create_conference_invalid_json(self):
        """Test per dati JSON non validi"""
        self.client.force_login(self.admin_user)

        session = self.client.session
        session['_auth_user_id'] = self.admin_user.id
        session.save()

        invalid_json_payload = "This is not JSON"
        response = self.client.post(self.url, data=invalid_json_payload, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Invalid JSON")

    def test_create_conference_invalid_method(self):
        """Test per metodo di richiesta non valido (non POST)"""
        self.client.force_login(self.admin_user)

        session = self.client.session
        session['_auth_user_id'] = self.admin_user.id
        session.save()

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

        self.url = reverse('delete_conference')

        self.client = Client()
        self.client.force_login(self.user)
        session = self.client.session
        session['_auth_user_id'] = self.user.id
        session.save()

    def test_delete_conference_as_admin(self):

        # Invia la richiesta per eliminare la conferenza
        response = self.client.delete(
            self.url,
            data={'conference_id': self.conference.id},
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
        session = self.client.session
        session['_auth_user_id'] = other_user.id
        session.save()

        # Invia la richiesta per eliminare la conferenza
        response = self.client.delete(
            self.url,
            data={'conference_id': self.conference.id},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {'error': 'Permission denied. User is not an admin of this conference.'})

        # Verifica che la conferenza non sia stata eliminata
        self.assertTrue(Conference.objects.filter(id=self.conference.id).exists())

    def test_delete_conference_with_missing_fields(self):

        # Invia la richiesta senza i campi obbligatori
        response = self.client.delete(
            self.url,
            data={},
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'Missing conference_id'})

        # Verifica che la conferenza non sia stata eliminata
        self.assertTrue(Conference.objects.filter(id=self.conference.id).exists())

    def test_delete_conference_with_invalid_json(self):

        # Invia la richiesta con un JSON non valido
        response = self.client.delete(
            self.url,
            data={'this is not a json'},
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'Invalid JSON'})

        # Verifica che la conferenza non sia stata eliminata
        self.assertTrue(Conference.objects.filter(id=self.conference.id).exists())

    def test_delete_conference_with_non_existent_conference(self):

        # Invia la richiesta per eliminare una conferenza inesistente
        response = self.client.delete(
            self.url,
            data={'conference_id': 999},
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'error': 'Conference not found'})

        # Verifica che la conferenza non sia stata eliminata
        self.assertTrue(Conference.objects.filter(id=self.conference.id).exists())





# -------------------------------------------------------------------------------------------------------------------------------------- #
#                       tests for edit_conference:


class EditConferenceTest(TestCase):
    def setUp(self):
        # Crea un utente e una conferenza di prova
        self.client = Client()
        self.user_admin = User.objects.create(first_name="Admin", last_name="User", email="admin@example.com",
                                              password="adminpass")
        self.user_non_admin = User.objects.create(first_name="NonAdmin", last_name="User", email="nonadmin@example.com",
                                                  password="nonadminpass")
        self.conference = Conference.objects.create(
            title="Test Conference",
            admin_id=self.user_admin,
            created_at=timezone.now(),
            deadline=timezone.now() + timezone.timedelta(days=10),
            description="Conference description"
        )
        
        self.client.force_login(self.user_admin)

        session = self.client.session
        session['_auth_user_id'] = self.user_admin.id
        session.save()

        # Assegna il ruolo di admin all'utente admin
        ConferenceRole.objects.create(user=self.user_admin, conference=self.conference, role='admin')

    def test_edit_conference_successful(self):
        # Modifica con dati validi da un utente admin
        response = self.client.patch(
            reverse('edit_conference'),  # Assicurati che il nome dell'URL sia corretto
            data=json.dumps({
                'conference_id': self.conference.id,
                'user_id': self.user_admin.id,
                'title': 'Updated Conference Title',
                'description': 'Updated description',
            }),
            content_type="application/json"

        )
        self.assertEqual(response.status_code, 200)
        self.conference.refresh_from_db()
        self.assertEqual(self.conference.title, 'Updated Conference Title')
        self.assertEqual(self.conference.description, 'Updated description')

    def test_edit_conference_permission_denied(self):
        # Attempt a modification by a non-admin user

        session = self.client.session
        session['_auth_user_id'] = 99999
        session.save()

        response = self.client.patch(
            reverse('edit_conference'),
            data=json.dumps({
                'conference_id': self.conference.id,
                'user_id': self.user_non_admin.id,
                'title': 'Should Not Update',
            }),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

        # Attempt to retrieve JSON content and verify 'error' key
        try:
            response_data = response.json()
        except ValueError:
            self.fail("Response did not return valid JSON content")

        # Check that 'error' key is present and contains the correct message
        self.assertIn('error', response_data, "Expected 'error' key in response")
        self.assertIn('User not found', response_data['error'])

    def test_edit_conference_not_found(self):
        # Conferenza con ID inesistente
        response = self.client.patch(
            reverse('edit_conference'),
            data=json.dumps({
                'conference_id': 9999,  # ID inesistente
                'user_id': self.user_admin.id,
                'title': 'Should Not Update',
            }),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn('Conference not found', response.json().get('error'))

    def test_edit_conference_missing_conference_id(self):
        # Richiesta senza `conference_id`
        response = self.client.patch(
            reverse('edit_conference'),
            data=json.dumps({
                'user_id': self.user_admin.id,
                'title': 'No Conference ID',
            }),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Missing conference_id', response.json().get('error'))

    def test_edit_conference_method_not_allowed(self):
        # Attempt to modify using a method other than PATCH
        response = self.client.post(
            reverse('edit_conference'),
            data=json.dumps({
                'conference_id': self.conference.id,
                'user_id': self.user_admin.id,
                'title': 'Should Not Update',
            }),
            content_type="application/json"
        )

        # Assert that the status code is 405
        self.assertEqual(response.status_code, 405)

        # Check that the response contains 'detail' rather than 'error'
        response_data = response.json()
        self.assertIsInstance(response_data, dict)  # Check if response is a dictionary
        self.assertIn('detail', response_data)  # Ensure 'detail' key is present
        self.assertEqual(response_data['detail'], 'Method "POST" not allowed.')  # Check specific message returned by DRF
        '''
        Or instead of the last lines we can use the following, to add flexibility to the test:
        self.assertIn('Method', response_data['detail'])
        self.assertIn('not allowed', response_data['detail'])
        '''
