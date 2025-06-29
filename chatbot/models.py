from django.db import models

# Create your models here.
from django.db import models
from stages.models import Etudiant, Entreprise

class ChatMessage(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    message = models.TextField()
    response = models.TextField()
    is_user_message = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    intent = models.CharField(max_length=100, blank=True, null=True)
    confidence = models.FloatField(blank=True, null=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.user.username}: {self.message[:50]}"
