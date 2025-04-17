from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from rest_framework.exceptions import ValidationError
from django.utils import timezone
import phonenumbers, random, string
from datetime import timedelta
import uuid

def normalize_phone_number(phone_number):
    """
    Normalizes phone numbers to international format with +98 prefix for Iran.
    
    Args:
        phone_number (str): Raw phone number in various formats
        
    Returns:
        str: Normalized phone number in international format
        
    Raises:
        ValidationError: If phone number format is invalid
    """
    # Handle various phone number formats
    if not phone_number.startswith("+98"):
        phone_number = ''.join(e for e in phone_number if e.isdigit())
    
    # Convert to international format with +98 prefix (Iran)
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
        # Parse and validate phone number using phonenumbers library
        parsed_number = phonenumbers.parse(phone_number, "IR")
        if not phonenumbers.is_valid_number(parsed_number):
            raise ValidationError({"error": "number is not valid"})
        
        # Format number in international format without spaces
        formatted_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL).replace(" ", "") 
        return formatted_number

    except phonenumbers.NumberParseException:
        raise ValidationError({"error": "number is not valid."})


class UserManager(BaseUserManager):
    """
    Custom user manager for the User model.
    Handles user creation and validation.
    """
    def create_user(self, phone_number, email, first_name, last_name, password=None, **extra_fields):
        """
        Creates and saves a new user with the given details.
        
        Args:
            phone_number (str): User's phone number
            email (str): User's email address
            first_name (str): User's first name
            last_name (str): User's last name
            password (str, optional): User's password
            **extra_fields: Additional fields for the user model
            
        Returns:
            User: The created user instance
        """
        if not phone_number:
            raise ValueError("شماره باید حتما وارد شود.")
        
        if not email:
            raise ValueError("ایمیل باید حتما وارد شود.")
        
        phone_number = normalize_phone_number(phone_number)
        user = self.model(
            phone_number=phone_number, 
            email=email, 
            first_name=first_name, 
            last_name=last_name, 
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone_number, email, first_name, last_name, password=None, **extra_fields):
        """
        Creates and saves a superuser with the given details.
        
        Args:
            phone_number (str): User's phone number
            email (str): User's email address
            first_name (str): User's first name
            last_name (str): User's last name
            password (str, optional): User's password
            **extra_fields: Additional fields for the user model
            
        Returns:
            User: The created superuser instance
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone_number, email, first_name, last_name, password, **extra_fields)


class User(AbstractBaseUser):
    """
    Custom user model with phone-based authentication.
    
    Uses phone number as the primary identifier for authentication.
    """
    phone_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=False)  # User must verify phone number to be active
    is_staff = models.BooleanField(default=False)   # Can access admin
    is_superuser = models.BooleanField(default=False)  # Has all permissions
    
    date_joined = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    # Fields used for authentication
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name', 'password']

    objects = UserManager()
    
    def save(self, *args, **kwargs):
        self.phone_number = normalize_phone_number(self.phone_number)
        super().save(*args, **kwargs)
    
    def __str__(self):
        """String representation of the user"""
        return f"{self.first_name} {self.last_name} - {self.phone_number}"


class OTPRequest(models.Model):
    """
    Model for managing one-time passwords (OTP) for various authentication flows.
    
    Handles OTP generation, expiration, and verification for user registration,
    password reset, and phone number verification.
    """
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
    expires_at = models.DateTimeField()  # When OTP becomes invalid
    refreshes_at = models.DateTimeField()  # When user can request a new OTP
    is_verified = models.BooleanField(default=False)  # Whether OTP has been verified
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPE_CHOICES, default="signup")
    
    def generate_otp(self):
        """Generate a random 6-digit OTP code"""
        return ''.join(random.choices(string.digits, k=6))
    
    def save(self, *args, **kwargs):
        """
        Set default values on save:
        - Generate OTP code if not provided
        - Set expiration and refresh timestamps
        - Normalize phone number
        """
        if not self.otp_code:
            self.otp_code = self.generate_otp()
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=5)  # OTP valid for 5 minutes
        if not self.refreshes_at:
            self.refreshes_at = timezone.now() + timedelta(minutes=2)  # Can request new OTP after 2 minutes
        
        self.phone_number = normalize_phone_number(self.phone_number)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Check if OTP has expired"""
        return timezone.now() > self.expires_at
    
    def is_refreshable(self):
        """Check if user can request a new OTP"""
        return timezone.now() > self.refreshes_at
    
    def __str__(self):
        """String representation of the OTP request"""
        return f"{self.phone_number} - {self.otp_code}"