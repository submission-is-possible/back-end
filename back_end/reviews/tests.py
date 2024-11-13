from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from reviews.models import Review
from users.models import User
from papers.models import Paper
from conference.models import Conference
import json

class GetUserReviewsTest(TestCase):
    def setUp(self):
        # Creazione di un utente di test
        self.user = User.objects.create(
            first_name="Test",
            last_name="User",
            email="testuser@example.com",
            password="testpassword"
        )
        
        # Creazione di una conferenza di test
        self.conference = Conference.objects.create(
            title="Test Conference",
            admin_id=self.user,
            created_at=timezone.now(),
            deadline=timezone.now() + timezone.timedelta(days=30),
            description="A test conference"
        )

        # Creazione di un paper di test
        self.paper = Paper.objects.create(
            title="Test Paper",
            paper_file=None,
            conference=self.conference,
            author_id=self.user,
            status_id="submitted"
        )

        # Creazione di alcune recensioni di test
        self.review1 = Review.objects.create(
            paper=self.paper,
            user=self.user,
            comment_text="Great paper!",
            score=5,
            created_at=timezone.now()
        )
        self.review2 = Review.objects.create(
            paper=self.paper,
            user=self.user,
            comment_text="Needs improvement.",
            score=3,
            created_at=timezone.now()
        )

        # URL per la funzione get_user_reviews
        self.url = reverse('get_user_reviews')
        self.client = Client()

    def test_get_user_reviews_success(self):
        """Test per una richiesta valida con un user_id e verifica della paginazione."""
        response = self.client.post(
            self.url,
            data=json.dumps({"user_id": self.user.id}),
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["total_reviews"], 2)
        self.assertEqual(data["reviews"][0]["comment_text"], "Great paper!")
        self.assertEqual(data["reviews"][1]["comment_text"], "Needs improvement.")
        self.assertEqual(data["current_page"], 1)
        self.assertEqual(data["total_pages"], 1)

    def test_get_user_reviews_invalid_method(self):
        """Test per verificare che una richiesta non-POST venga rifiutata con status 405."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        #self.assertEqual(response.json(), {"error": "Only POST requests are allowed"})
        #anche se ho modificato il messaggio di errore, django di default restituisce un messaggio di errore diverso,
        #quindi il test fallirà. 
        self.assertEqual(response.json(), {"detail": "Method \"GET\" not allowed."})

    def test_get_user_reviews_missing_user_id(self):
        """Test per verificare la gestione di una richiesta senza user_id."""
        response = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Missing user_id"})

    def test_get_user_reviews_invalid_json(self):
        """Test per verificare la gestione di una richiesta con JSON non valido."""
        response = self.client.post(self.url, data="Invalid JSON", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Invalid JSON"})

    def test_get_user_reviews_pagination(self):
        """Test per verificare la corretta paginazione."""
        # Creazione di altre recensioni per verificare la paginazione
        for i in range(15):
            Review.objects.create(
                paper=self.paper,
                user=self.user,
                comment_text=f"Review {i}",
                score=4,
                created_at=timezone.now()
            )

        response = self.client.post(
            f"{self.url}?page=2&page_size=10",
            data=json.dumps({"user_id": self.user.id}),
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # La seconda pagina dovrebbe contenere 7 recensioni (17 totali, 10 nella prima pagina)
        self.assertEqual(data["current_page"], 2)
        self.assertEqual(len(data["reviews"]), 7)
        self.assertEqual(data["total_reviews"], 17)
        self.assertEqual(data["total_pages"], 2)
