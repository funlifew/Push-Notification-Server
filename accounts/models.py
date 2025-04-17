from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from rest_framework.exceptions import ValidationError
from django.utils import timezone
import phonenumbers, random, string
from datetime import timedelta
import uuid

# Create your models here.

def normalize_phone_number(phone_number):
    if not phone_number.startswith("+98"):
        phone_number = ''.join(e for e in phone_number if e.isdigit())
    
    if phone_number.startswith("0098"):
        phone_number = "+98" + phone_number[4:]
    elif phone_number.startswith("0"):
        phone_number = "+98" + phone_number[1:]
    elif phone_number.startswith("9"):
        phone_number = "+98" + phone_number
    elif phone_number.startswith("+98"):
        pass
    else:
        raise ValidationError("فرمت شماره موبایل صحیح نیست.")
        
    try:
    # پارس کردن شماره تلفن با استفاده از phonenumbers
        parsed_number = phonenumbers.parse(phone_number, "IR")
        if not phonenumbers.is_valid_number(parsed_number):
            raise ValidationError({"error": "number is not valid"})
        
        formatted_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL).replace(" ", "") 
        return formatted_number

    except phonenumbers.NumberParseException:
        raise ValidationError({"error": "number is not valid."})

class UserManager(BaseUserManager):

    def create_user(self, phone_number, email, first_name, last_name, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("شماره باید حتما وارد شود.")
        
        if not email:
            raise ValueError("ایمیل باید حتما وارد شود.")
        
        phone_number = normalize_phone_number(phone_number)
        user = self.model(phone_number = phone_number, email=email, first_name=first_name, last_name=last_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone_number, email, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone_number, email, first_name, last_name, **extra_fields)

class User(AbstractBaseUser):
    phone_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    date_joined = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name', 'password']

    objects = UserManager()
    
    # def save(self, *args, **kwargs):
    #     self.phone_number = normalize_phone_number(self.phone_number)
    #     super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.phone_number}"


class OTPRequest(models.Model):
    REQUEST_TYPE_CHOICES = (
        ("signup", "Signup"),
        ("password_reset", "Password Reset"),
        ("phone_verification", "Phone Verification")
    )
    register_id = models.UUIDField(unique=True, primary_key=True, default=uuid.uuid4)
    phone_number = models.CharField(max_length=20)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    refreshes_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPE_CHOICES, default="signup")

    
    
    def generate_otp(self):
        return ''.join(random.choices(string.digits, k=6))
    
    def save(self, *args, **kwargs):
        if not self.otp_code:
            self.otp_code = self.generate_otp()
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=5)
        if not self.refreshes_at:
            self.refreshes_at = timezone.now() + timedelta(minutes=2)
        
        self.phone_number = normalize_phone_number(self.phone_number)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    def is_refreshable(self):
        return timezone.now() > self.refreshes_at
    
    def __str__(self):
        return f"{self.phone_number} - {self.otp_code}"
