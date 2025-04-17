from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from .models import normalize_phone_number

class PhoneAuthBackend(ModelBackend):
    """
    Custom authentication backend that supports login with both:
    - Email address
    - Phone number (in various formats)
    
    This enables users to log in using either their email or phone number
    along with their password.
    """
    
    def user_can_authenticate(self, user):
        """
        Allow all users to authenticate, regardless of is_active status.
        
        Note: Although this method allows authentication, views can still
        check is_active and require OTP verification before granting access.
        
        Args:
            user: The user attempting to authenticate
            
        Returns:
            bool: True for all users
        """
        return True
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate users by email or phone number.
        
        Args:
            request: The HTTP request
            username: Email address or phone number
            password: User's password
            **kwargs: Additional arguments
            
        Returns:
            User: The authenticated user or None
        """
        if username is None:
            return None
        
        user = None
        
        # Check if username contains @ symbol (email)
        if "@" in username:
            # Try to find user by email
            user = get_user_model().objects.filter(email=username).first()
        else:
            # Try to find user by phone number
            try:
                # Normalize the phone number format
                try:
                    normalize_phone = normalize_phone_number(username)
                except:
                    return None
                    
                # Find user with normalized phone number
                user = get_user_model().objects.filter(phone_number=normalize_phone).first()
            except ValueError:
                return None

        # Verify password if user exists
        if user and user.check_password(password):
            return user
        else:
            return None