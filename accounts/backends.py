from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from .models import User, normalize_phone_number
import re

class PhoneAuthBackend(ModelBackend):
    def user_can_authenticate(self, user):
        return True
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            return None
        
        user = None
        
        

        if "@" in username:
            user = get_user_model().objects.filter(email=username).first()
        
        else:
            try:
                try:
                    normalize_phone = normalize_phone_number(username)
                except:
                    return None
                user = get_user_model().objects.filter(phone_number = normalize_phone).first()
            except ValueError:
                return None

        if user and user.check_password(password):
            return user
        else:
            return None