
# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class Document(models.Model):
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('error', 'Error'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='pdfs/')
    title = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')

    def __str__(self):
        return self.title or self.file.name

class ChatMessage(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='messages')
    user_question = models.TextField()
    ai_response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
