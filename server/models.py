from django.db import models
from django.utils import timezone
import uuid, string, random

def generate_random_name():
    """
    Generate a random 20-character string for token names.
    Used as default for AdminToken name field.
    
    Returns:
        str: Random string of letters and digits
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=20))


class AdminToken(models.Model):
    """
    Model for API authentication tokens used by administrators.
    
    Each token has:
    - A unique UUID identifier
    - A human-readable name (random by default)
    - A timestamp of when it was created
    
    These tokens are used to authenticate push notification API requests.
    """
    # UUID token for API authorization
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    # Human-readable name for the token
    name = models.CharField(max_length=20, default=generate_random_name)
    
    # When the token was created
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        """
        String representation showing name and last 10 characters of token
        for easy identification without exposing the full token.
        """
        return f"{self.name} - {self.token}"[-10:]