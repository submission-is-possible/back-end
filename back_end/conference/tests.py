import json
from django.urls import reverse
from django.utils import timezone
from django.test import TestCase, Client
from rest_framework.test import APITestCase

from .models import User, Conference
from conference_roles.models import ConferenceRole
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
        """Test for successful conference creation with all required fields"""
        payload = {
            "title": "Test Conference",
            "admin_id": self.admin_user.id,
            "deadline": (timezone.now() + timezone.timedelta(days=7)).isoformat(),
            "description": "Description of the test conference",
            "authors": [self.author.email],
            "reviewers": [self.reviewer.email]
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

        # Verify roles creation
        self.assertTrue(
            ConferenceRole.objects.filter(
                conference=conference,
                user=self.admin_user,
                role='admin'
            ).exists()
        )
        self.assertTrue(
            ConferenceRole.objects.filter(
                conference=conference,
                user=self.author,
                role='author'
            ).exists()
        )
        self.assertTrue(
            ConferenceRole.objects.filter(
                conference=conference,
                user=self.reviewer,
                role='reviewer'
            ).exists()
        )

        # Verify notifications
        self.assertTrue(
            Notification.objects.filter(
                conference=conference,
                user_sender=self.admin_user,
                user_receiver=self.author,
                type=0
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                conference=conference,
                user_sender=self.admin_user,
                user_receiver=self.reviewer,
                type=1
            ).exists()
        )

    def test_create_conference_missing_fields(self):
        """Test for missing required fields"""
        payload = {
            "title": "Test Conference",
            "admin_id": self.admin_user.id,
            # Missing deadline, description, authors, and reviewers
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Missing fields")

    def test_create_conference_invalid_admin(self):
        """Test for invalid admin ID"""
        payload = {
            "title": "Test Conference",
            "admin_id": 9999,
            "deadline": (timezone.now() + timezone.timedelta(days=7)).isoformat(),
            "description": "Description of the test conference",
            "authors": [self.author.email],
            "reviewers": [self.reviewer.email]
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "Admin user not found")

    def test_create_conference_invalid_author(self):
        """Test for invalid author email"""
        payload = {
            "title": "Test Conference",
            "admin_id": self.admin_user.id,
            "deadline": (timezone.now() + timezone.timedelta(days=7)).isoformat(),
            "description": "Description of the test conference",
            "authors": ["nonexistent@example.com"],
            "reviewers": [self.reviewer.email]
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "Author user not found")

    def test_create_conference_invalid_reviewer(self):
        """Test for invalid reviewer email"""
        payload = {
            "title": "Test Conference",
            "admin_id": self.admin_user.id,
            "deadline": (timezone.now() + timezone.timedelta(days=7)).isoformat(),
            "description": "Description of the test conference",
            "authors": [self.author.email],
            "reviewers": ["nonexistent@example.com"]
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "Reviewer user not found")

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

    def test_delete_conference_as_admin(self):
        """Test successful conference deletion by admin"""
        response = self.client.delete(
            reverse('delete_conference'),
            data=json.dumps({
                'conference_id': self.conference.id,
                'user_id': self.user.id
            }),
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
        
        response = self.client.delete(
            reverse('delete_conference'),
            data=json.dumps({
                'conference_id': self.conference.id,
                'user_id': other_user.id
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(),
            {'error': 'Permission denied. User is not an admin of this conference.'}
        )

    def test_delete_conference_missing_fields(self):
        """Test deletion attempt with missing required fields"""
        response = self.client.delete(
            reverse('delete_conference'),
            data=json.dumps({}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'Missing required fields'})

    def test_delete_conference_conference_not_found(self):
        """Test deletion attempt for non-existent conference"""
        response = self.client.delete(
            reverse('delete_conference'),
            data=json.dumps({
                'conference_id': 9999,
                'user_id': self.user.id
            }),
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
        # Assign admin role
        ConferenceRole.objects.create(
            user=self.user_admin,
            conference=self.conference,
            role='admin'
        )

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
        """Test edit attempt by non-admin user"""
        response = self.client.patch(
            reverse('edit_conference'),
            data=json.dumps({
                'conference_id': self.conference.id,
                'user_id': self.user_non_admin.id,
                'title': 'Should Not Update',
            }),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn('Permission denied', response.json()['error'])

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
        self.assertEqual(response.json()['error'], 'Missing conference_id')