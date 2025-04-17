from kavenegar import *
from decouple import config
import json, re, os
from rest_framework.exceptions import ValidationError
from pywebpush import webpush, WebPushException

VAPID_CLAIMS = {
    "sub": config("VAPID_SUBJECT"),
}

VAPID_PRIVATE_KEY = config("VAPID_PRIVATE_KEY")

def send_web_push(subscription_info, message):
    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(message),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims = VAPID_CLAIMS
        )
        
        return {"success": True}
    
    except WebPushException as ex:
        return {"success": False, "error": str(ex)}
        

def validate_phone_number(phone_number):
    pattern = re.compile(r"^(?:\+98|0098|98|0|9)?9\d{9}$")
    if not pattern.match(phone_number):
        raise ValidationError("شماره موبایل معتبر نیست.")
    return phone_number

def send_otp(phone_number, otp_code):
    try:
        api = KavenegarAPI(config("KAVENEGAR_API"))
        
        params = {
            'receptor': phone_number,
            'template': "pushnotificationserver",
            'token': otp_code,
            'type': "sms",
        }
        
        response = api.verify_lookup(params)
        return response
    except APIException as e:
        return str(e)
    except HTTPException as e:
        return str(e)