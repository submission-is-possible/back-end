from django.db import models
from django.utils import timezone

class User(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)

    #Questo campo viene utilizzato per memorizzare la data e l'ora dell'ultimo accesso dell'utente.
    last_login = models.DateTimeField(null=True, blank=True)
    #questo consente al campo di avere valori nulli. Se l'utente non ha mai effettuato il login, il valore di last_login rimarrà nullo.
    #Questo campo è fondamentale per tenere traccia dell'ultima volta che l'utente ha effettuato il login. 
    # Quando si chiama la funzione login(request, user), Django aggiorna automaticamente questo campo. Se non è presente, si genera un errore, come hai visto nel test fallito.

    def __str__(self):
        return f"{self.first_name} {self.last_name}"