from django.db import models


from django.db import models

class Notification(models.Model):
    id_user1 = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='sent_notifications') # utente che invia la notifica, chiave esterna al modello User
    id_user2 = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='received_notifications') # utente che riceve la notifica, chiave esterna al modello User
    #possible types: 'invited_as_reviewer', 'invited_as_author', 'reviewer_accepted_invite', 'author_accepted_invite', 'reviewer_declined_invite', 'author_declined_invite'
    type = models.CharField(max_length=100) # tipo di notifica
    description = models.TextField() # descrizione (testo) della notifica
    title = models.CharField(max_length=100) # titolo (oggetto) della notifica
    creation_date = models.DateTimeField(auto_now_add=True) # data di creazione della notifica creata automaticamente
    read = models.BooleanField(default=False) # indica se la notifica è stata letta o meno

    def __str__(self):
        return f"{self.title} - {self.description} - {self.id_user1} - {self.id_user2}"
