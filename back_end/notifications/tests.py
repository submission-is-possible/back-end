from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .models import User, Conference, Notification
import json
from django.core.paginator import Paginator


class NotificationTests(TestCase):
    def setUp(self):
        # Creare utenti per i test
        self.user_sender = User.objects.create(
            first_name="Sender",
            last_name="User",
            email="sender@example.com",
            password="password123"
        )

        self.user_receiver = User.objects.create(
            first_name="Receiver",
            last_name="User",
            email="receiver@example.com",
            password="password123"
        )

        # Creare una conferenza per i test
        self.conference = Conference.objects.create(
            title="Test Conference",
            admin_id=self.user_sender,
            deadline=timezone.now() + timezone.timedelta(days=7),
            description="Test Conference Description"
        )

    def test_create_notification_successful(self):
        """Test per la creazione di una notifica con dati validi"""
        url = reverse('create_notification')
        payload = {
            "user_sender": {"id": self.user_sender.id},
            "user_receiver": {"id": self.user_receiver.id},
            "conference": {"id": self.conference.id},
            "type": 0  # author type
        }

        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["message"], "Notification created successfully")
        self.assertIn("notification_id", response.json())

        # Verifica che la notifica sia stata creata nel database
        notification = Notification.objects.get(id=response.json()["notification_id"])
        self.assertEqual(notification.user_sender, self.user_sender)
        self.assertEqual(notification.user_receiver, self.user_receiver)
        self.assertEqual(notification.conference, self.conference)
        self.assertEqual(notification.type, 0)
        self.assertEqual(notification.status, 0)

    def test_create_notification_missing_fields(self):
        """Test per la creazione di una notifica con campi mancanti"""
        url = reverse('create_notification')
        payload = {
            "user_sender": {"id": self.user_sender.id},
            # user_receiver mancante
            "conference": {"id": self.conference.id},
            "type": 0
        }

        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Missing fields")

    def test_create_notification_invalid_user_sender(self):
        """Test per la creazione di una notifica con user_sender non esistente"""
        url = reverse('create_notification')
        payload = {
            "user_sender": {"id": 99999},  # ID non esistente
            "user_receiver": {"id": self.user_receiver.id},
            "conference": {"id": self.conference.id},
            "type": 0
        }

        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "User sender not found")

    def test_get_notifications_received_successful(self):
        """Test per ottenere le notifiche ricevute da un utente"""
        # Creare alcune notifiche di test
        Notification.objects.create(
            user_sender=self.user_sender,
            user_receiver=self.user_receiver,
            conference=self.conference,
            type=0, # author type
            status=0 # pending status
        )

        url = reverse('get_notifications_received') # URL per ottenere le notifiche ricevute
        payload = {
            "user_id": self.user_receiver.id
        }

        response = self.client.post(
            url,
            data=json.dumps(payload), # Converti il payload in JSON
            content_type="application/json" # Il tipo di contenuto è JSON
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("notifications", response.json())
        self.assertIn("total_notifications", response.json())
        self.assertIn("current_page", response.json())
        self.assertIn("total_pages", response.json())

    def test_delete_notification_successful(self):
        """Test per l'eliminazione di una notifica"""
        notification = Notification.objects.create(
            user_sender=self.user_sender,
            user_receiver=self.user_receiver,
            conference=self.conference,
            type=0,
            status=0
        )

        url = reverse('delete_notification')
        payload = {
            "user_id": self.user_receiver.id,
            "id_notification": notification.id
        }

        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Notification deleted successfully")

        # Verifica che la notifica sia stata eliminata
        with self.assertRaises(Notification.DoesNotExist):
            Notification.objects.get(id=notification.id)

    def test_delete_notification_not_found(self):
        """Test per l'eliminazione di una notifica non esistente"""
        url = reverse('delete_notification')
        payload = {
            "user_id": self.user_receiver.id,
            "id_notification": 99999  # ID non esistente
        }

        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "Notification not found or does not belong to the user")

    def test_update_notification_successful(self):
        """Test per l'aggiornamento dello stato di una notifica"""
        notification = Notification.objects.create(
            user_sender=self.user_sender,
            user_receiver=self.user_receiver,
            conference=self.conference,
            type=0,
            status=0
        )

        url = reverse('update_notification')
        payload = {
            "id_notification": notification.id,
            "status": "accept"
        }

        response = self.client.patch(
            url,
            data=json.dumps(payload),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Notification updated successfully")

        # Verifica che lo stato sia stato aggiornato
        updated_notification = Notification.objects.get(id=notification.id)
        self.assertEqual(updated_notification.status, 1)  # 1 = accepted
        self.assertEqual(updated_notification.user_sender, self.user_receiver)
        self.assertEqual(updated_notification.user_receiver, self.user_sender)

    def test_update_notification_invalid_status(self):
        """Test per l'aggiornamento con uno stato non valido"""
        notification = Notification.objects.create(
            user_sender=self.user_sender,
            user_receiver=self.user_receiver,
            conference=self.conference,
            type=0,
            status=0
        )

        url = reverse('update_notification')
        payload = {
            "id_notification": notification.id,
            "status": "invalid_status"
        }

        response = self.client.patch(
            url,
            data=json.dumps(payload),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Invalid status value")