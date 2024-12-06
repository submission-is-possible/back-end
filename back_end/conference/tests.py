import json
from django.urls import reverse
from django.utils import timezone
from django.test import TestCase, Client
from rest_framework.test import APITestCase

from .models import Conference
from users.models import User
from conference_roles.models import ConferenceRole
from papers.models import Paper
from assign_paper_reviewers.models import PaperReviewAssignment
from preferences.models import Preference
from notifications.models import Notification

class ConferenceCreationTests(TestCase):
    def setUp(self):
        # Create admin user and additional users for testing
        self.admin_user = User.objects.create(
            first_name="Admin",
            last_name="User",
            email="admin@example.com",
            password="securepassword"
        )
        self.author = User.objects.create(
            first_name="Author",
            last_name="User",
            email="author@example.com",
            password="authorpass"
        )
        self.reviewer = User.objects.create(
            first_name="Reviewer",
            last_name="User",
            email="reviewer@example.com",
            password="reviewerpass"
        )
        self.url = reverse('create_conference')

    def test_create_conference_successful(self):
        """Test per la creazione di una conferenza con dati validi"""
        self.client.force_login(self.admin_user)
        session = self.client.session
        session['_auth_user_id'] = self.admin_user.id
        session.save()
        payload = {
            "title": "Test Conference",
            "deadline": (timezone.now() + timezone.timedelta(days=7)).isoformat(),
            "description": "Description of the test conference",
            "reviewers": [{"email": self.reviewer.email}],
            "papers_deadline": (timezone.now() + timezone.timedelta(days=5)).isoformat(),
            "status": "none"
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["message"], "Conference created successfully")
        self.assertIn("conference_id", response.json())

        # Verify conference creation
        conference = Conference.objects.get(id=response.json()["conference_id"])
        self.assertEqual(conference.title, payload["title"])
        self.assertEqual(conference.admin_id, self.admin_user)

        # Verify admin role creation
        self.assertTrue(
            ConferenceRole.objects.filter(
                conference=conference,
                user=self.admin_user,
                role='admin'
            ).exists()
        )

        # Verify notification creation for reviewer
        self.assertTrue(
            Notification.objects.filter(
                conference=conference,
                user_sender=self.admin_user,
                user_receiver=self.reviewer,
                type=1,  # reviewer type
                status=0  # pending status
            ).exists()
        )

        # Verify no reviewer role is created initially
        self.assertFalse(
            ConferenceRole.objects.filter(
                conference=conference,
                user=self.reviewer,
                role='reviewer'
            ).exists()
        )
        

    def test_create_conference_missing_fields(self):
        """Test per mancanza di campi obbligatori"""

        self.client.force_login(self.admin_user)

        session = self.client.session
        session['_auth_user_id'] = self.admin_user.id
        session.save()

        payload = {
            "title": "Test Conference",
            "admin_id": self.admin_user.id,
            # Missing deadline, description, authors, reviewers and status
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Missing required fields")

    def test_create_conference_invalid_admin(self):
        """Test per ID admin non valido"""

        self.client.force_login(self.admin_user)

        session = self.client.session
        session['_auth_user_id'] = 9999
        session.save()

        payload = {
            "title": "Test Conference",
            "admin_id": 9999,  # Un ID che non esiste
            "deadline": (timezone.now() + timezone.timedelta(days=7)).isoformat(),
            "description": "Description of the test conference",
            "authors": [self.author.email],
            "reviewers": [self.reviewer.email]
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
        
    def test_create_conference_invalid_reviewer(self):
        """Test for invalid reviewer email"""

        self.client.force_login(self.admin_user)

        session = self.client.session
        session['_auth_user_id'] = self.admin_user.id
        session.save()

        payload = {
            "title": "Test Conference",
            "deadline": (timezone.now() + timezone.timedelta(days=7)).isoformat(),
            "description": "Description of the test conference",
            "reviewers": [{"email": "nonexistent@example.com"}]  # Lista di dizionari
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
    
    def test_create_conference_invalid_status(self):
        """Test for invalid status value"""

        self.client.force_login(self.admin_user)

        session = self.client.session
        session['_auth_user_id'] = self.admin_user.id
        session.save()

        payload = {
            "title": "Test Conference",
            "deadline": (timezone.now() + timezone.timedelta(days=7)).isoformat(),
            "description": "Description of the test conference",
            "reviewers": [{"email": self.reviewer.email}],
            "status": "invalid_status"
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'Missing required fields')

class DeleteConferenceTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Create test user
        self.user = User.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password="password"
        )
        
        # Create test conference
        self.conference = Conference.objects.create(
            title="Test Conference",
            admin_id=self.user,
            deadline="2023-12-31 23:59:59",
            description="This is a test conference"
        )
        
        # Create conference role
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
        self.assertFalse(Conference.objects.filter(id=self.conference.id).exists())

    def test_delete_conference_without_permission(self):
        """Test deletion attempt by non-admin user"""
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

class EditConferenceTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Create admin user
        self.user_admin = User.objects.create(
            first_name="Admin",
            last_name="User",
            email="admin@example.com",
            password="adminpass"
        )
        # Create non-admin user
        self.user_non_admin = User.objects.create(
            first_name="NonAdmin",
            last_name="User",
            email="nonadmin@example.com",
            password="nonadminpass"
        )
        # Create test conference
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
        """Test successful conference edit by admin"""
        response = self.client.patch(
            reverse('edit_conference'),
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
        """Test edit attempt for non-existent conference"""
        response = self.client.patch(
            reverse('edit_conference'),
            data=json.dumps({
                'conference_id': 9999,
                'user_id': self.user_admin.id,
                'title': 'Should Not Update',
            }),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['error'], 'Conference not found')

    def test_edit_conference_missing_fields(self):
        """Test edit attempt with missing required fields"""
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

class GetConferencesTestCase(TestCase):
    def setUp(self):
        # Create a user for admin
        self.user = User.objects.create(
            first_name="Test",
            last_name="Admin",
            email="test_admin@example.com",
            password="testpassword"
        )

        # Create multiple conferences for testing pagination
        for i in range(25):
            Conference.objects.create(
                title=f"Conference {i+1}",
                admin_id=self.user,
                created_at=timezone.now(),
                deadline=timezone.now() + timezone.timedelta(days=10),
                description=f"Description for Conference {i+1}"
            )

    def test_get_conferences_default_pagination(self):
        """Test default pagination (20 conferences per page)"""
        response = self.client.get(reverse('get_conferences'))
        
        self.assertEqual(response.status_code, 200)
        
        # Parse the response JSON
        response_data = json.loads(response.content)
        
        # Check pagination details
        self.assertEqual(response_data['current_page'], 1)
        self.assertEqual(response_data['total_pages'], 2)
        self.assertEqual(response_data['total_conferences'], 25)
        self.assertEqual(len(response_data['conferences']), 20)

    def test_get_conferences_specific_page(self):
        """Test retrieving a specific page"""
        response = self.client.get(reverse('get_conferences') + '?page=2')
        
        self.assertEqual(response.status_code, 200)
        
        # Parse the response JSON
        response_data = json.loads(response.content)
        
        # Check pagination details
        self.assertEqual(response_data['current_page'], 2)
        self.assertEqual(response_data['total_pages'], 2)
        self.assertEqual(response_data['total_conferences'], 25)
        self.assertEqual(len(response_data['conferences']), 5)

    def test_get_conferences_custom_page_size(self):
        """Test custom page size"""
        response = self.client.get(reverse('get_conferences') + '?page_size=10')
        
        self.assertEqual(response.status_code, 200)
        
        # Parse the response JSON
        response_data = json.loads(response.content)
        
        # Check pagination details
        self.assertEqual(response_data['current_page'], 1)
        self.assertEqual(response_data['total_pages'], 3)
        self.assertEqual(response_data['total_conferences'], 25)
        self.assertEqual(len(response_data['conferences']), 10)

    
class AutomaticAssignReviewersTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create(first_name='Admin', last_name='User', email='admin@example.com', password='adminpass')
        self.reviewer1 = User.objects.create(first_name='Reviewer', last_name='One', email='reviewer1@example.com', password='reviewerpass1')
        self.reviewer2 = User.objects.create(first_name='Reviewer', last_name='Two', email='reviewer2@example.com', password='reviewerpass2')
        self.reviewer3 = User.objects.create(first_name='Reviewer', last_name='Three', email='reviewer3@example.com', password='reviewerpass3')

        self.conference = Conference.objects.create(
            title='Test Conference',
            admin_id=self.admin,
            deadline=timezone.now() + timezone.timedelta(days=30),
            description='This is a test conference',
            papers_deadline=timezone.now() + timezone.timedelta(days=15),
            automatic_assign_status=False
        )

        ConferenceRole.objects.create(user=self.admin, conference=self.conference, role='admin')
        ConferenceRole.objects.create(user=self.reviewer1, conference=self.conference, role='reviewer')
        ConferenceRole.objects.create(user=self.reviewer2, conference=self.conference, role='reviewer')
        ConferenceRole.objects.create(user=self.reviewer3, conference=self.conference, role='reviewer')

        self.paper1 = Paper.objects.create(title='Paper 1', conference=self.conference, author_id=self.admin, status_id='submitted')
        self.paper2 = Paper.objects.create(title='Paper 2', conference=self.conference, author_id=self.admin, status_id='submitted')
        self.paper3 = Paper.objects.create(title='Paper 3', conference=self.conference, author_id=self.admin, status_id='submitted')

        Preference.objects.create(paper=self.paper1, reviewer=self.reviewer1, preference='interested')
        Preference.objects.create(paper=self.paper1, reviewer=self.reviewer2, preference='interested')
        Preference.objects.create(paper=self.paper2, reviewer=self.reviewer2, preference='interested')
        Preference.objects.create(paper=self.paper2, reviewer=self.reviewer3, preference='interested')
        Preference.objects.create(paper=self.paper3, reviewer=self.reviewer1, preference='interested')
        Preference.objects.create(paper=self.paper3, reviewer=self.reviewer3, preference='interested')

    def test_automatic_assign_reviewers(self):
        client = Client()
        response = client.post('/conference/automatic_assign_reviewers/', json.dumps({
            'user_id': self.admin.id,
            'conference_id': self.conference.id,
            'max_papers_per_reviewer': 2,
            'required_reviewers_per_paper': 2
        }), content_type='application/json')

        self.assertEqual(response.status_code, 201)
        self.assertIn('message', response.json())
        self.assertEqual(response.json()['message'], 'Reviewers assigned successfully.')

        self.conference.refresh_from_db()
        self.assertTrue(self.conference.automatic_assign_status)

        assignments = PaperReviewAssignment.objects.filter(conference=self.conference)
        self.assertTrue(assignments.exists())
        self.assertEqual(assignments.count(), 6)

        for paper in [self.paper1, self.paper2, self.paper3]:
            self.assertEqual(assignments.filter(paper=paper).count(), 2)