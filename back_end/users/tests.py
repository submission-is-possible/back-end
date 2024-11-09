from django.test import TestCase, Client
from django.contrib.auth.hashers import make_password
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
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.assertIn('detail', response.json())
        self.assertEqual(response.json()['detail'], 'Method "GET" not allowed.')




class LoginUserTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('login')
        
        # Crea l'utente di test con la password hashata
        self.user = User.objects.create(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            password=make_password("securepassword123")  # Usa make_password per hasharla
        )

    #verifica il login con credenziali corrette.
    def test_login_success(self):
        data = {
            "email": "john.doe@example.com",
            "password": "securepassword123"
        }
        response = self.client.post(self.url, json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Login successful", response.json().get("message"))

    #verifica il login con credenziali errate.
    def test_login_invalid_credentials(self):
        data = {
            "email": "john.doe@example.com",
            "password": "wrongpassword"
        }
        response = self.client.post(self.url, json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid email or password", response.json().get("error"))

    #verifica la mancanza di campi obbligatori.
    def test_login_missing_fields(self):
        data = {
            "email": "john.doe@example.com"
        }
        response = self.client.post(self.url, json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Email and password are required.", response.json().get("error"))

    #verifica che solo le richieste POST siano accettate.
    def test_login_invalid_method(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json()['detail'], 'Method "GET" not allowed.')