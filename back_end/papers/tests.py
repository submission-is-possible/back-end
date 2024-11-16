from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.urls import reverse
from .models import Paper
from users.models import User
from conference.models import Conference
import json
import base64
from datetime import timedelta
import os
import shutil
from unittest.mock import patch
from django.conf import settings

class PaperTests(TestCase):
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create test user with all required fields
        self.user = User.objects.create(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            password="testpassword123"
        )
        
        # Create another user as conference admin
        self.admin_user = User.objects.create(
            first_name="Admin",
            last_name="User",
            email="admin@example.com",
            password="adminpassword123"
        )
        
        # Create test conference with all required fields
        self.conference = Conference.objects.create(
            title="Test Conference",
            admin_id=self.admin_user,
            deadline=timezone.now() + timedelta(days=30),  # Set deadline 30 days from now
            description="This is a test conference for paper submissions"
        )
        
        # Create sample PDF content
        self.sample_pdf_content = b"Sample PDF content"
        self.encoded_pdf = base64.b64encode(self.sample_pdf_content).decode('utf-8')
        
        # Valid paper data - note we're using author_id directly
        self.valid_paper_data = {
            'title': 'Test Paper',
            'paper_file': self.encoded_pdf,
            'conference_id': self.conference.id
        }

        # Set up test papers directory
        self.test_papers_dir = os.path.join(settings.BASE_DIR, 'test_media', 'test_papers')
        os.makedirs(self.test_papers_dir, exist_ok=True)

        # Mock MEDIA_ROOT for tests
        self.patcher = patch('django.conf.settings.MEDIA_ROOT', self.test_papers_dir)
        self.mock_media_root = self.patcher.start()


        # Set up test papers directory
        self.test_papers_dir = os.path.join(settings.BASE_DIR, 'test_media', 'test_papers')
        os.makedirs(self.test_papers_dir, exist_ok=True)

        # Mock MEDIA_ROOT for tests
        self.patcher = patch('django.conf.settings.MEDIA_ROOT', self.test_papers_dir)
        self.mock_media_root = self.patcher.start()



    def test_successful_paper_creation(self):
        # Prepare test data

        self.client.force_login(self.user)
        session = self.client.session
        session['_auth_user_id'] = self.user.id
        session.save()
    
        paper_data = {
            'title': 'Test Paper',
            'paper_file': self.encoded_pdf,
            'author': self.user.id,
            'conference': self.conference.id
        }

        # Send request
        response = self.client.post(
            reverse('create_paper'),
            data=json.dumps(paper_data),
            content_type='application/json'
        )

        # Verify response
        self.assertEqual(response.status_code, 201)

    def test_missing_fields(self):
        """Test paper creation with missing required fields."""
        # Test missing title
        self.client.force_login(self.user)
        session = self.client.session
        session['_auth_user_id'] = self.user.id
        session.save()

        invalid_data = self.valid_paper_data.copy()
        del invalid_data['title']
        response = self.client.post(
            reverse('create_paper'),
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        
        # Test missing conference_id
        invalid_data = self.valid_paper_data.copy()
        del invalid_data['conference']
        response = self.client.post(
            reverse('create_paper'),
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_author_id(self):
        """Test paper creation with non-existent author ID."""

        self.client.force_login(self.user)
        session = self.client.session
        session['_auth_user_id'] = 99999
        session.save()

        invalid_data = self.valid_paper_data.copy()
        response = self.client.post(
            reverse('create_paper'),
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'User not found', response.content)

    def test_invalid_conference_id(self):
        """Test paper creation with non-existent conference ID."""

        self.client.force_login(self.user)
        session = self.client.session
        session['_auth_user_id'] = self.user.id
        session.save()
        
        invalid_data = self.valid_paper_data.copy()
        invalid_data['conference'] = 99999  # Non-existent ID
        response = self.client.post(
            reverse('create_paper'),
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn(b'Conference not found', response.content)

    def test_invalid_request_method(self):
        """Test paper creation with invalid HTTP method."""
        response = self.client.get(reverse('create_paper'))
        self.assertEqual(response.status_code, 405)
    
    def tearDown(self):
        """Clean up test data."""
        # Stop the patcher
        self.patcher.stop()

        # Remove test directory and contents
        if os.path.exists(self.test_papers_dir):
            shutil.rmtree(os.path.dirname(self.test_papers_dir))

class ListPapersTests(TestCase):
    def setUp(self):
        """Create test user, conference, and papers for testing"""
        # Create test user
        self.user = User.objects.create(
            first_name="Mario",
            last_name="Rossi",
            email="mariorossi@gmail.com",
            password="password123"
        )

        # Create test conference
        self.conference = Conference.objects.create(
            title="AI Conference",
            admin_id=self.user,
            deadline=timezone.now() + timezone.timedelta(days=30),
            description="A conference on AI advancements."
        )

        # Create test papers
        self.paper1 = Paper.objects.create(
            title="First Test Paper",
            author_id=self.user,
            conference=self.conference,
            status_id='submitted'
        )
        
        self.paper2 = Paper.objects.create(
            title="Second Test Paper",
            author_id=self.user,
            conference=self.conference,
            status_id='accepted'
        )

        # Set up the URL and default payload
        self.url = reverse('list_papers')
        self.valid_payload = {
            "user_id": self.user.id
        }

        # Set up test papers directory
        self.test_papers_dir = os.path.join(settings.BASE_DIR, 'test_media', 'test_papers')
        os.makedirs(self.test_papers_dir, exist_ok=True)

        # Mock MEDIA_ROOT for tests
        self.patcher = patch('django.conf.settings.MEDIA_ROOT', self.test_papers_dir)
        self.mock_media_root = self.patcher.start()

    def test_list_papers_with_pagination(self):
        """Test pagination functionality"""

        for i in range(8):
            Paper.objects.create(
                title=f"Paper {i+3}",
                author_id=self.user,
                conference=self.conference,
                status_id='submitted'
            )

        # Test first page with 5 items
        response = self.client.post(
            f"{self.url}?page=1&page_size=5",
            data=self.valid_payload,
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)

    def test_successful_paper_listing(self):
        """Test basic paper listing functionality."""
        response = self.client.post(
            self.url,
            data=json.dumps({"user_id": self.user.id}),
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertEqual(data['total_papers'], 2)  # Two papers created in setUp
        self.assertTrue('papers' in data)
        self.assertTrue('current_page' in data)
        self.assertTrue('total_pages' in data)

    def test_pagination(self):
        """Test pagination functionality."""
        # Test with custom page size
        page_size = 2
        response = self.client.post(
            f"{self.url}?page=1&page_size={page_size}",
            data=json.dumps({"user_id": self.user.id}),
            content_type="application/json"
        )
        
        data = json.loads(response.content)
        self.assertEqual(len(data['papers']), 2)  # Only 2 papers exist
        self.assertEqual(data['current_page'], 1)
        
        # Test last page
        last_page = data['total_pages']
        response = self.client.post(
            f"{self.url}?page={last_page}&page_size={page_size}",
            data=json.dumps({"user_id": self.user.id}),
            content_type="application/json"
        )
        
        data = json.loads(response.content)
        self.assertEqual(data['current_page'], last_page)
        self.assertLessEqual(len(data['papers']), page_size)

    def test_user_specific_papers(self):
        """Test that only papers belonging to the specified user are returned."""
        response = self.client.post(
            self.url,
            data=json.dumps({"user_id": self.user.id}),
            content_type="application/json"
        )
        
        data = json.loads(response.content)
        self.assertEqual(data['total_papers'], 2)  # User has 2 papers from setUp
        
        # Verify paper titles belong to user
        expected_titles = ["First Test Paper", "Second Test Paper"]
        paper_titles = [paper['title'] for paper in data['papers']]
        self.assertEqual(set(paper_titles), set(expected_titles))

    def test_invalid_user_id(self):
        """Test response when invalid user ID is provided."""
        response = self.client.post(
            self.url,
            data=json.dumps({"user_id": 99999}),  # Non-existent user ID
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'User not found')

    def test_missing_user_id(self):
        """Test response when user ID is missing from request."""
        response = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Missing user_id')

    def test_invalid_request_method(self):
        """Test response for non-POST requests."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        
        response = self.client.put(
            self.url,
            data=json.dumps({"user_id": self.user.id}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 405)

    def test_invalid_json(self):
        """Test response when invalid JSON is sent."""
        response = self.client.post(
            self.url,
            data="invalid json",
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Invalid JSON')

    def test_paper_response_structure(self):
        """Test that each paper in the response has the correct structure."""
        response = self.client.post(
            self.url,
            data=json.dumps({"user_id": self.user.id}),
            content_type="application/json"
        )
        
        data = json.loads(response.content)
        paper = data['papers'][0]
        
        required_fields = {
            'id', 'title', 'paper_file', 'conference',
            'conference_title', 'status', 'created_at'
        }
        
        self.assertEqual(set(paper.keys()), required_fields)
    
    def tearDown(self):
        """Clean up test data."""
        # Stop the patcher
        self.patcher.stop()

        # Remove test directory and contents
        if os.path.exists(self.test_papers_dir):
            shutil.rmtree(os.path.dirname(self.test_papers_dir))

class ViewPaperPDFTests(TestCase):
    def setUp(self):
        """Set up test environment."""
        self.client = Client()
        
        # Set up test papers directory
        self.test_papers_dir = os.path.join(settings.BASE_DIR, 'test_media', 'test_papers')
        os.makedirs(self.test_papers_dir, exist_ok=True)

        # Mock MEDIA_ROOT for tests
        self.patcher = patch('django.conf.settings.MEDIA_ROOT', self.test_papers_dir)
        self.mock_media_root = self.patcher.start()# Create test media directory structure
        self.test_media_root = os.path.join(settings.BASE_DIR, 'test_media')
        self.test_papers_dir = os.path.join(self.test_media_root, 'papers', 'paper')
        os.makedirs(self.test_papers_dir, exist_ok=True)
        
        # Create a test PDF file
        self.test_pdf_content = b"%PDF-1.4\ntest pdf content"
        self.test_filename = "test_paper.pdf"
        self.test_filepath = os.path.join(self.test_papers_dir, self.test_filename)
        
        try:
            with open(self.test_filepath, 'wb') as f:
                f.write(self.test_pdf_content)
        except Exception as e:
            print(f"Error creating test PDF file: {e}")
            
    def tearDown(self):
        """Clean up test environment."""
        # Remove test media directory and all contents
        if os.path.exists(self.test_media_root):
            shutil.rmtree(self.test_media_root)

    @patch('django.conf.settings.MEDIA_ROOT', new_callable=lambda: os.path.join(settings.BASE_DIR, 'test_media'))
    def test_successful_pdf_view(self, mock_media_root):
        """Test successful PDF file viewing."""
        response = self.client.get(reverse('view_paper_pdf', args=[self.test_filename]))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertEqual(response['Content-Disposition'], f'inline; filename="{self.test_filename}"')
        self.assertEqual(response['Cache-Control'], 'public, max-age=3600')
        
        # Read the streaming content
        content = b''.join(response.streaming_content)
        self.assertEqual(content, self.test_pdf_content)

    @patch('django.conf.settings.MEDIA_ROOT', new_callable=lambda: os.path.join(settings.BASE_DIR, 'test_media'))
    def test_file_not_found(self, mock_media_root):
        """Test response when PDF file doesn't exist."""
        response = self.client.get(reverse('view_paper_pdf', args=['nonexistent.pdf']))
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['error'], 'File not found: nonexistent.pdf')

    @patch('django.conf.settings.MEDIA_ROOT', new_callable=lambda: os.path.join(settings.BASE_DIR, 'test_media'))
    def test_invalid_file_type(self, mock_media_root):
        """Test response when file is not a PDF."""
        # Create a non-PDF file
        non_pdf_path = os.path.join(self.test_papers_dir, 'test.txt')
        with open(non_pdf_path, 'w') as f:
            f.write('test content')
            
        response = self.client.get(reverse('view_paper_pdf', args=['test.txt']))
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'Invalid file type')

    @patch('django.conf.settings.MEDIA_ROOT', new_callable=lambda: os.path.join(settings.BASE_DIR, 'test_media'))
    def test_filename_sanitization(self, mock_media_root):
        """Test that filenames are properly sanitized."""
        # Create file with special characters
        special_filename = 'test!@#$%^&*().pdf'
        special_filepath = os.path.join(self.test_papers_dir, os.path.basename(special_filename))
        with open(special_filepath, 'wb') as f:
            f.write(self.test_pdf_content)
            
        response = self.client.get(reverse('view_paper_pdf', args=[special_filename]))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_invalid_request_method(self):
        """Test response for non-GET requests."""
        response = self.client.post(reverse('view_paper_pdf', args=['test.pdf']))
        self.assertEqual(response.status_code, 405)
    
    def tearDown(self):
        """Clean up test environment."""
        # Stop the patcher
        self.patcher.stop()

        # Remove test directory and contents
        if os.path.exists(self.test_papers_dir):
            shutil.rmtree(os.path.dirname(self.test_papers_dir)) 