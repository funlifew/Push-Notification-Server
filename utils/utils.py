import json
import re
import os
from io import BytesIO
from PIL import Image
from decouple import config
from kavenegar import KavenegarAPI, APIException, HTTPException
from rest_framework.exceptions import ValidationError
from pywebpush import webpush, WebPushException

# Configuration constants
VAPID_CLAIMS = {
    "sub": config("VAPID_SUBJECT"),
}
VAPID_PRIVATE_KEY = config("VAPID_PRIVATE_KEY")

def resize_and_compress_image(image, max_size=(64, 64), quality=85):
    """
    Resize and compress an image to optimize it for use as a notification icon.
    
    Args:
        image: The uploaded image file
        max_size: Maximum dimensions (width, height) for the resized image
        quality: JPEG compression quality (0-100)
        
    Returns:
        BytesIO: A buffer containing the compressed image
    """
    try:
        img = Image.open(image)
        
        # Maintain aspect ratio while resizing
        img.thumbnail(max_size)
        
        # Convert to RGB if necessary (e.g., PNG with transparency)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        
        # Save to buffer with compression
        output = BytesIO()
        img.save(output, format="JPEG", quality=quality, optimize=True)
        output.seek(0)
        return output
    except Exception as e:
        print(f"Error processing image: {e}")
        raise ValueError(f"Failed to process image: {str(e)}")

def send_web_push(subscription_info, message):
    """
    Send a web push notification to a subscription.
    
    Args:
        subscription_info: The push subscription information
        message: The notification message (will be JSON-encoded)
        
    Returns:
        dict: Result with success status and any error information
    """
    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(message),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS
        )
        return {"success": True}
    except WebPushException as ex:
        print(f"Web push error: {str(ex)}")
        return {"success": False, "error": str(ex)}
    except Exception as ex:
        print(f"Unexpected error in web push: {str(ex)}")
        return {"success": False, "error": f"Unexpected error: {str(ex)}"}

def validate_phone_number(phone_number):
    """
    Validate an Iranian phone number format.
    
    Args:
        phone_number: The phone number to validate
        
    Returns:
        str: The validated phone number
        
    Raises:
        ValidationError: If the phone number format is invalid
    """
    if not phone_number:
        raise ValidationError("شماره موبایل نمی‌تواند خالی باشد.")
        
    # Regex for Iranian mobile numbers
    pattern = re.compile(r"^(?:\+98|0098|98|0|9)?9\d{9}$")
    
    if not pattern.match(phone_number):
        raise ValidationError("شماره موبایل معتبر نیست.")
    
    return phone_number

def send_otp(phone_number, otp_code):
    """
    Send an OTP code via SMS using Kavenegar API.
    
    Args:
        phone_number: The recipient's phone number
        otp_code: The OTP code to send
        
    Returns:
        dict/str: API response or error message
    """
    try:
        # Initialize Kavenegar API with the API key
        api = KavenegarAPI(config("KAVENEGAR_API"))
        
        # Prepare parameters for the verification lookup
        params = {
            'receptor': phone_number,
            'template': "pushnotificationserver",
            'token': otp_code,
            'type': "sms",
        }
        
        # Send the OTP via the API
        response = api.verify_lookup(params)
        return response
    except APIException as e:
        print(f"Kavenegar API error: {str(e)}")
        return {"success": False, "error": str(e)}
    except HTTPException as e:
        print(f"HTTP error in Kavenegar API: {str(e)}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        print(f"Unexpected error in OTP sending: {str(e)}")
        return {"success": False, "error": f"Unexpected error: {str(e)}"}