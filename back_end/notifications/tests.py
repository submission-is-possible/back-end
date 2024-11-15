from datetime import timedelta
import json

from django.urls import reverse
from django.utils import timezone
from django.test import TestCase, Client
from .models import User, Conference, Notification

class NotificationTestCase(TestCase):
    def setUp(self):
        # Crea utenti di test
        self.user_sender = User.objects.create(
            first_name="Sender", last_name="User", email="sender@example.com", password="password"
        )
        self.user_receiver = User.objects.create(
            first_name="Receiver", last_name="User", email="receiver@example.com", password="password"
        )

        # Crea una conferenza di test
        self.conference = Conference.objects.create(
            title="Test Conference",
            admin_id=self.user_sender,
            deadline=timezone.now() + timezone.timedelta(days=7),
            description="This is a test conference"
        )

    def test_create_notification_successful(self):
        # Effettua il login dell'utente sender
        self.client.force_login(self.user_sender)

        # Invia la richiesta per creare una nuova notifica
        payload = {
            "user_receiver": {
                "id": self.user_receiver.id,
                "first_name": self.user_receiver.first_name,
                "last_name": self.user_receiver.last_name,
                "email": self.user_receiver.email,
                "password": self.user_receiver.password
            },
            "conference": {
                "id": self.conference.id,
                "title": self.conference.title,
                "admin_id": self.conference.admin_id.id,
                "created_at": self.conference.created_at.isoformat(),
                "deadline": self.conference.deadline.isoformat(),
                "description": self.conference.description
            },
            "type": 0
        }
        response = self.client.post(reverse('create_notification'), data=json.dumps(payload),
                                    content_type="application/json")

        #self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["message"], "Notification created successfully")
        self.assertIn("notification_id", response.json())

        # Verifica che la notifica sia stata creata correttamente
        notification = Notification.objects.get(id=response.json()["notification_id"])
        self.assertEqual(notification.user_sender, self.user_sender)
        self.assertEqual(notification.user_receiver, self.user_receiver)
        self.assertEqual(notification.conference, self.conference)
        self.assertEqual(notification.type, 0)

    def test_get_notifications_received(self):
        # Crea alcune notifiche per l'utente receiver
        Notification.objects.create(
            user_sender=self.user_sender,
            user_receiver=self.user_receiver,
            conference=self.conference,
            status=0,
            type=0,
            created_at=timezone.now()
        )
        Notification.objects.create(
            user_sender=self.user_sender,
            user_receiver=self.user_receiver,
            conference=self.conference,
            status=1,
            type=1,
            created_at=timezone.now() - timezone.timedelta(days=2)
        )

        # Effettua il login dell'utente receiver
        self.client.force_login(self.user_receiver)

        # Invia la richiesta per ottenere le notifiche ricevute
        response = self.client.post(reverse('get_notifications_received'), data=json.dumps({"user_id": self.user_receiver.id}), content_type="application/json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["notifications"]), 2)

        # Verifica i campi delle notifiche nella risposta
        notifications = response.json()["notifications"]
        self.assertEqual(notifications[0]["user_sender"]["id"], self.user_sender.id)
        self.assertEqual(notifications[0]["user_receiver"]["id"], self.user_receiver.id)
        self.assertEqual(notifications[0]["conference"]["id"], self.conference.id)
        self.assertEqual(notifications[0]["status"], "pending")
        self.assertEqual(notifications[0]["type"], "author")

        self.assertEqual(notifications[1]["user_sender"]["id"], self.user_sender.                                                                                                                                                                                                                                                                                                                                                     d)
        self.assertEqual(notifications[1]["user_receiver"]["id"], self.user_receiver.id)
        self.assertEqual(notifications[1]["conference"]["id"], self.conference.id)
        self.assertEqual(notifications[1]["status"], "accepted")
        self.assertEqual(notifications[1]["type"], "reviewer")

    def test_delete_notification(self):
        # Crea una notifica per l'utente receiver
        notification = Notification.objects.create(
            user_sender=self.user_sender,
            user_receiver=self.user_receiver,
            conference=self.conference,
            status=0,
            type=0,
            created_at=timezone.now()
        )

        # Effettua il login dell'utente receiver
        self.client.force_login(self.user_receiver)

        # Invia la richiesta per eliminare la notifica
        response = self.client.post(reverse('delete_notification'), data=json.dumps({
            "user_id": self.user_receiver.id,
            "id_notification": notification.id
        }), content_type="application/json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Notification deleted successfully")

        # Verifica che la notifica sia stata eliminata
        self.assertFalse(Notification.objects.filter(id=notification.id).exists())

    def test_update_notification(self):
        # Crea una notifica per l'utente receiver
        notification = Notification.objects.create(
            user_sender=self.user_sender,
            user_receiver=self.user_receiver,
            conference=self.conference,
            status=0,
            type=0,
            created_at=timezone.now()
        )

        # Effettua il login dell'utente receiver
        self.client.force_login(self.user_receiver)

        # Invia la richiesta per aggiornare la notifica
        response = self.client.patch(reverse('update_notification'), data=json.dumps({
            "id_notification": notification.id,
            "status": "accept"
        }), content_type="application/json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Notification updated successfully")

        # Verifica che la notifica sia stata aggiornata correttamente
        updated_notification = Notification.objects.get(id=notification.id)
        self.assertEqual(updated_notification.status, 1)
        self.assertEqual(updated_notification.user_sender, self.user_receiver)
        self.assertEqual(updated_notification.user_receiver, self.user_sender)