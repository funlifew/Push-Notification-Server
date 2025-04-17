from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.views import Response, APIView
from utils.utils import resize_and_compress_image
from .models import AdminToken
import json, base64, uuid
from pywebpush import webpush, WebPushException
from decouple import config
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.core.files.uploadedfile import InMemoryUploadedFile

# Allowed image formats
ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png', 'image/jpg']

def convert_to_base64(file):
    """Convert a file to base64 encoding for embedding in notification."""
    try:
        with file.open('rb') as f:
            encoded_string = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{file.content_type};base64,{encoded_string}"
    except Exception as e:
        print(f"Error converting file to base64: {e}")
        return None

def prepare_notification_payload(title, body, url=None, icon=None):
    """Prepare a consistent notification payload format."""
    payload = {
        "title": title,
        "body": body,
        "url": url,
        "requireInteraction": True,  # Keep notification visible until user interaction
        "data": {
            "url": url  # For click handling in service worker
        }
    }
    
    if icon:
        payload["icon"] = icon
        
    return json.dumps(payload)

class GenerateAdminTokenView(APIView):
    def post(self, request):
        token = AdminToken.objects.create()
        return Response({
            "token": str(token.token),
            "name": token.name
        }, status=status.HTTP_201_CREATED)

class SendSingleNotificationView(APIView):
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    def post(self, request):
        # Validate admin token
        admin_token = request.data.get("admin_token")
        if not admin_token:
            return Response({"admin_token": "required field"}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not AdminToken.objects.filter(token=admin_token).exists():
            return Response({"admin_token": "admin_token is invalid"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get notification parameters
        try:
            subscription_info = json.loads(request.data.get("subscription_info", "{}"))
        except json.JSONDecodeError:
            return Response({"subscription_info": "invalid JSON format"}, status=status.HTTP_400_BAD_REQUEST)
        
        title = request.data.get('title')
        body = request.data.get("body")
        url = request.data.get("url")
        icon = request.FILES.get("icon")

        # Validate required fields
        if not subscription_info:
            return Response({"subscription_info": "is a required field"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not title or not body:
            return Response({"error": "Title and body are required fields"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Process icon if provided
        icon_base64 = None
        if icon:
            # Validate icon mime type
            if icon.content_type not in ALLOWED_MIME_TYPES:
                return Response({
                    "error": "Unsupported file type. Only JPEG and PNG are allowed."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Resize and compress
            try:
                compressed_image = resize_and_compress_image(icon)
                compressed_file = InMemoryUploadedFile(
                    compressed_image,
                    None,
                    f"{uuid.uuid4()}.jpg",  # Unique name with jpg extension
                    'image/jpeg',
                    compressed_image.getbuffer().nbytes,
                    None
                )
                icon_base64 = convert_to_base64(compressed_file)
            except Exception as e:
                print(f"Error processing image: {e}")
                # Continue without the icon if processing fails
        
        # Prepare and send notification
        payload = prepare_notification_payload(title, body, url, icon_base64)
        
        try:
            webpush(
                subscription_info,
                data=payload,
                vapid_private_key=config("VAPID_PRIVATE_KEY"),
                vapid_claims={"sub": config("VAPID_SUBJECT")}
            )
            return Response({"message": "Notification sent successfully"}, status=status.HTTP_200_OK)
        except WebPushException as ex:
            return Response({"error": str(ex)}, status=status.HTTP_400_BAD_REQUEST)

class SendGroupNotificationView(APIView):
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    def post(self, request):
        # Validate admin token
        admin_token = request.data.get("admin_token")
        if not admin_token:
            return Response({"admin_token": "required field"}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not AdminToken.objects.filter(token=admin_token).exists():
            return Response({"admin_token": "admin_token is invalid"}, status=status.HTTP_401_UNAUTHORIZED)

        # Get notification parameters
        try:
            subscription_list_str = request.data.get("subscription_info_list", "[]")
            subscription_info_list = json.loads(subscription_list_str)
            
            if not isinstance(subscription_info_list, list) or not subscription_info_list:
                return Response({
                    "subscription_info_list": "Must be a non-empty list"
                }, status=status.HTTP_400_BAD_REQUEST)
        except json.JSONDecodeError:
            return Response({
                "subscription_info_list": "Invalid JSON format"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        title = request.data.get("title")
        body = request.data.get("body")
        url = request.data.get("url")
        icon = request.FILES.get("icon")
        
        # Validate required fields
        if not title or not body:
            return Response({"error": "Title and body are required fields"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Process icon if provided
        icon_base64 = None
        if icon:
            # Validate icon mime type
            if icon.content_type not in ALLOWED_MIME_TYPES:
                return Response({
                    "error": "Unsupported file type. Only JPEG and PNG are allowed."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Resize and compress
            try:
                compressed_image = resize_and_compress_image(icon)
                compressed_file = InMemoryUploadedFile(
                    compressed_image,
                    None,
                    f"{uuid.uuid4()}.jpg",  # Unique name with jpg extension
                    'image/jpeg',
                    compressed_image.getbuffer().nbytes,
                    None
                )
                icon_base64 = convert_to_base64(compressed_file)
            except Exception as e:
                print(f"Error processing image: {e}")
                # Continue without the icon if processing fails
        
        # Prepare notification payload
        payload = prepare_notification_payload(title, body, url, icon_base64)
        
        # Send to all subscriptions
        errors = []
        successes = []
        
        for subscription_info in subscription_info_list:
            try:
                webpush(
                    subscription_info,
                    data=payload,
                    vapid_private_key=config("VAPID_PRIVATE_KEY"),
                    vapid_claims={"sub": config("VAPID_SUBJECT")}
                )
                successes.append(subscription_info.get('endpoint', 'unknown'))
            except WebPushException as ex:
                errors.append(subscription_info.get('endpoint', 'unknown'))
                print(f"Error sending to {subscription_info.get('endpoint', 'unknown')}: {str(ex)}")
        
        return Response({
            'success': successes,
            'error': errors,
            'total': len(subscription_info_list),
            'success_count': len(successes),
            'error_count': len(errors)
        }, status=status.HTTP_200_OK)