from django.db import models
from django.utils import timezone
import uuid, string, random

def generate_random_name():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=20))


class AdminToken(models.Model):
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=20, default=generate_random_name)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.token[10:]}"
