from django.db import models

# Create your models here.

class Note(models.Model):
    userId = models.CharField(max_length=128)
    topic = models.CharField(max_length=256)
    notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.userId} - {self.topic} ({self.created_at})"
