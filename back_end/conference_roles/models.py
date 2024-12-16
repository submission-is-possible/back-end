from django.db import models
from users.models import User
from conference.models import Conference  # Importa Conference se si trova nella stessa app o specifica l'app corretta

class ConferenceRole(models.Model):
    ROLE_CHOICES = [
        ('author', 'Author'),
        ('reviewer', 'Reviewer'),
        ('admin', 'Admin')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="conference_roles")
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name="conference_roles")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    
    def __str__(self):
        return f"{self.user} - {self.conference.title} ({self.role})"
