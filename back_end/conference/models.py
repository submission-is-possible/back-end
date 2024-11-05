from django.db import models
from users.models import User  # Importa User se `User` è in un'app chiamata "users"

class Conference(models.Model):
    title = models.CharField(max_length=200)  # Titolo della conferenza
    admin_id = models.ForeignKey(User, on_delete=models.CASCADE)  # Chiave esterna al modello User
    created_at = models.DateTimeField(auto_now_add=True)  # Data di creazione (impostata automaticamente)
    deadline = models.DateTimeField()  # Deadline specifica per la conferenza
    description = models.TextField()  # Descrizione della conferenza

    def __str__(self):
        return self.title