from kavenegar import *
from decouple import config
import json, re
from rest_framework.exceptions import ValidationError
from pywebpush import webpush, WebPushException

# Web Push configuration from environment variables
VAPID_CLAIMS = {
    "sub": config("VAPID_SUBJECT"),  # mailto: email address
}
VAPID_PRIVATE_KEY = config("VAPID_PRIVATE_KEY")

def send_web_push(subscription_info, message):
    """
    Send a web push notification to a specific subscriber.
    
    Args:
        subscription_info (dict): Subscriber information including endpoint, keys
        message (dict): Notification content (title, body, icon, etc.)
        
    Returns:
        dict: Status of push notification delivery
        
    Example:
        send_web_push(
            subscription_info={
                "endpoint": "https://fcm.googleapis.com/fcm/send/...",
                "keys": {
                    "p256dh": "base64-encoded-key",
                    "auth": "base64-encoded-auth"
                }
            },
            message={
                "title": "New Notification",
                "body": "This is a notification message"
            }
        )
    """
    try:
        response = webpush(
            subscription_info=subscription_info,
            data=json.dumps(message),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS
        )
        
        return {"success": True}
    
    except WebPushException as ex:
        return {"success": False, "error": str(ex)}


def validate_phone_number(phone_number):
    """
    Validate an Iranian phone number format using regex.
    
    Args:
        phone_number (str): Phone number to validate
        
    Returns:
        str: The validated phone number
        
    Raises:
        ValidationError: If phone number format is invalid
    """
    # Pattern matches Iranian mobile numbers in various formats
    pattern = re.compile(r"^(?:\+98|0098|98|0|9)?9\d{9}$")
    if not pattern.match(phone_number):
        raise ValidationError("شماره موبایل معتبر نیست.")
    return phone_number


def send_otp(phone_number, otp_code):
    """
    Send OTP code via SMS using Kavenegar API.
    
    Args:
        phone_number (str): Recipient's phone number
        otp_code (str): The OTP code to send
        
    Returns:
        dict or str: API response or error message
        
    Example:
        send_otp("+989123456789", "123456")
    """
    try:
        # Initialize Kavenegar API client
        api = KavenegarAPI(config("KAVENEGAR_API"))
        
        # Configure parameters for the verification SMS
        params = {
            'receptor': phone_number,
            'template': "pushnotificationserver",  # Template name in Kavenegar panel
            'token': otp_code,
            'type': "sms",
        }
        
        # Send the verification SMS
        response = api.verify_lookup(params)
        return response
    except APIException as e:
        # Handle API errors (wrong API key, etc.)
        return str(e)
    except HTTPException as e:
        # Handle HTTP errors (connection issues, etc.)
        return str(e)