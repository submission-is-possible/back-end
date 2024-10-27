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

    
