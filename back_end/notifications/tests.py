from django.test import TestCase, Client
from django.urls import reverse
from notifications.models import Notification
from users.models import User
from django.utils import timezone
import json


class NotificationTests(TestCase):
    def setUp(self):
        # Crea utenti di test
        self.user1 = User.objects.create(
            first_name='John',
            last_name='Doe',
            email='john.doe@test.com',
            password='password123'
        )
        self.user2 = User.objects.create(
            first_name='Jane',
            last_name='Smith',
            email='jane.smith@test.com',
            password='password456'
        )
        self.client = Client()

        # Crea una notifica di esempio
        self.notification = Notification.objects.create(
            id_user1=self.user1,
            id_user2=self.user2,
            type='info',
            description='Test notification',
            title='Test Title',
            read=False
        )

    def test_create_notification(self):
        """Test creazione notifica"""
        url = reverse('create_notification')
        data = {
            'id_user1': self.user1.id,
            'id_user2': self.user2.id,
            'type': 'warning',
            'description': 'New test notification',
            'title': 'New Title',
            'read': False,
            'creation_date': timezone.now().isoformat()
        }

        response = self.client.post(
            url,
            json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Notification.objects.filter(title='New Title').exists())

    def test_get_notifications(self):
        """Test recupero notifiche per un utente"""
        url = reverse('get_notifications')
        data = {'user_id': self.user2.id}

        response = self.client.post(
            url,
            json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data['notifications']), 1)
        self.assertEqual(response_data['notifications'][0]['title'], 'Test Title')

    def test_mark_as_read(self):
        """Test marcatura notifica come letta"""
        url = reverse('mark_as_read')
        data = {'notification_id': self.notification.id}

        response = self.client.post(
            url,
            json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        updated_notification = Notification.objects.get(id=self.notification.id)
        self.assertTrue(updated_notification.read)

    def test_delete_notification(self):
        """Test eliminazione notifica"""
        url = reverse('delete_notification')
        data = {'notification_id': self.notification.id}

        response = self.client.post(
            url,
            json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Notification.objects.filter(id=self.notification.id).exists())

    def test_get_notifications_pagination(self):
        """Test paginazione notifiche"""
        # Crea 21 notifiche per garantire 3 pagine (con 10 elementi per pagina)
        # Nota: una notifica è già stata creata nel setUp()
        for i in range(20):
            Notification.objects.create(
                id_user1=self.user1,
                id_user2=self.user2,
                type='info',
                description=f'Test notification {i}',
                title=f'Test Title {i}',
                read=False
            )

        url = reverse('get_notifications')
        data = {'user_id': self.user2.id}

        response = self.client.post(
            url,
            json.dumps(data),
            content_type='application/json'
        )

        response_data = json.loads(response.content)
        # Con 21 notifiche totali e 10 per pagina, ci aspettiamo 3 pagine
        self.assertEqual(response_data['total_pages'], 3)
        # Verifica che nella prima pagina ci siano 10 notifiche
        self.assertEqual(len(response_data['notifications']), 10)

        # Verifica seconda pagina
        data['page'] = 2
        response = self.client.post(
            url,
            json.dumps(data),
            content_type='application/json'
        )
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data['notifications']), 10)

        # Verifica terza pagina
        data['page'] = 3
        response = self.client.post(
            url,
            json.dumps(data),
            content_type='application/json'
        )
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data['notifications']), 1)  # Ultima pagina con 1 notifica

    def test_invalid_user(self):
        """Test gestione di ID utente non valido"""
        url = reverse('get_notifications')
        data = {'user_id': 999}  # ID utente inesistente

        response = self.client.post(
            url,
            json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 404)  # Cambiato da 200 a 404

    def test_invalid_notification(self):
        """Test gestione di ID notifica non valido"""
        url = reverse('mark_as_read')
        data = {'notification_id': 999}  # ID notifica inesistente

        response = self.client.post(
            url,
            json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 404)  # Cambiato da 405 a 404

    def test_missing_fields(self):
        """Test gestione di campi obbligatori mancanti"""
        url = reverse('create_notification')
        data = {
            'id_user1': self.user1.id,
            # Campi mancanti
        }

        response = self.client.post(
            url,
            json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

    def test_invalid_method(self):
        """Test gestione metodi HTTP non validi"""
        urls = [
            reverse('create_notification'),
            reverse('get_notifications'),
            reverse('mark_as_read'),
            reverse('delete_notification')
        ]

        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 405)

    def test_create_notification_with_invalid_user(self):
        """Test creazione notifica con utente non valido"""
        url = reverse('create_notification')
        data = {
            'id_user1': 999,  # ID utente non esistente
            'id_user2': self.user2.id,
            'type': 'warning',
            'description': 'Test notification',
            'title': 'Test Title',
            'read': False,
            'creation_date': timezone.now().isoformat()
        }

        response = self.client.post(
            url,
            json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 404)

    def test_notification_fields(self):
        """Test campi della notifica"""
        notification = Notification.objects.get(id=self.notification.id)

        self.assertEqual(notification.id_user1, self.user1)
        self.assertEqual(notification.id_user2, self.user2)
        self.assertEqual(notification.type, 'info')
        self.assertEqual(notification.title, 'Test Title')
        self.assertEqual(notification.description, 'Test notification')
        self.assertFalse(notification.read)

