from django.test import TestCase, Client
from .models import User
from django.urls import reverse
import json

class CreateUserTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('create_user')  # Assicurati che questo corrisponda al tuo URL

    def test_create_user_success(self):
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "password": "securepassword123"
        }
        response = self.client.post(reverse('create_user'), json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(User.objects.count(), 1)

    def test_create_user_duplicate_email(self):
        User.objects.create(first_name="John", last_name="Doe", email="john.doe@example.com", password="pass123")
        data = {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "password": "securepassword123"
        }
        response = self.client.post(reverse('create_user'), json.dumps(data), content_type="application/json")
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("Email already in use", response.json().get("error"))
    
    def test_create_user_missing_fields(self):
        """Test errore per campi mancanti nella richiesta."""
        response = self.client.post(self.url, data=json.dumps({
            'first_name': 'John',
            'email': 'john.doe@example.com',
            'password': 'password123'
        }), content_type='application/json')  # manca il campo last_name

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'Missing fields')

    def test_create_user_invalid_json(self):
        """Test errore per JSON non valido."""
        response = self.client.post(self.url, data="Invalid JSON", content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'Invalid JSON')

    def test_create_user_invalid_method(self):
        """Test errore per metodo non POST."""
        response = self.client.get(self.url)  # Usa GET invece di POST

        self.assertEqual(response.status_code, 405)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'Only POST requests are allowed')
