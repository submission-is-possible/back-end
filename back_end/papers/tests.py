from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.urls import reverse
from .models import Paper
from users.models import User
from conference.models import Conference
import json

class PaperTests(TestCase):
    def setUp(self):
        """Set up test data before each test method"""
        # Create a test user (author)
        self.user = User.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password="testpass123"
        )
        
        # Create a test conference
        self.conference = Conference.objects.create(
            title="Test Conference 2024",
            admin_id=self.user,
            deadline=timezone.now() + timezone.timedelta(days=30),
            description="Ielo spara 100 per forza senza riprendere fiato"
        )
        
        # Create a test file
        self.test_file = SimpleUploadedFile(
            "test_paper.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        
        # Initialize the test client
        self.client = Client()

    def test_paper_creation_success(self):
        """Test successful paper creation"""
        data = {
            'title': 'Test Paper',
            'paper_file': self.test_file,
            'author_id': self.user.id,
            'conference_id': self.conference.id
        }
        
        response = self.client.post(reverse('create_paper'), data)
        
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Paper.objects.filter(title='Test Paper').exists())
        
        # Verify response content
        content = json.loads(response.content)
        self.assertIn('paper_id', content)
        self.assertEqual(content['message'], 'Paper added successfully')
        
        # Verify paper data in database
        paper = Paper.objects.get(title='Test Paper')
        self.assertEqual(paper.author, self.user)
        self.assertEqual(paper.conference, self.conference)
        self.assertEqual(paper.status, 'submitted')

    def test_paper_creation_missing_fields(self):
        """Test paper creation with missing fields"""
        # Test without title
        data = {
            'paper_file': self.test_file,
            'author_id': self.user.id,
            'conference_id': self.conference.id
        }
        
        response = self.client.post(reverse('create_paper'), data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content)['error'], 'Missing fields')

    def test_paper_creation_invalid_ids(self):
        """Test paper creation with invalid IDs"""
        # Test with non-existent author ID
        data = {
            'title': 'Test Paper',
            'paper_file': self.test_file,
            'author_id': 99999,
            'conference_id': self.conference.id
        }
        
        response = self.client.post(reverse('create_paper'), data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(json.loads(response.content)['error'], 'Author not found')

        # Test with non-existent conference ID
        data['author_id'] = self.user.id
        data['conference_id'] = 99999
        
        response = self.client.post(reverse('create_paper'), data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(json.loads(response.content)['error'], 'Conference not found')

    def test_paper_creation_invalid_id_format(self):
        """Test paper creation with invalid ID format"""
        data = {
            'title': 'Test Paper',
            'paper_file': self.test_file,
            'author_id': 'invalid',  # String instead of integer
            'conference_id': self.conference.id
        }
        
        response = self.client.post(reverse('create_paper'), data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content)['error'], 'Invalid ID format')

    def tearDown(self):
        """Clean up after each test"""
        # Delete test file if it exists
        if hasattr(self, 'test_file'):
            self.test_file.close()