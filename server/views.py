from django.shortcuts import render
from rest_framework import status
from rest_framework.views import Response, APIView
from rest_framework.permissions import IsAuthenticated
from .models import AdminToken
import json
from pywebpush import webpush, WebPushException
from decouple import config

class GenerateAdminTokenView(APIView):
    """
    API view for generating new admin tokens.
    
    Creates a new AdminToken with a unique UUID and random name.
    Returns the token value and name to the client.
    """
    def post(self, request):
        """
        POST method to generate a new admin token.
        
        Returns:
            Response: JSON with token and name
        """
        # Create a new token
        token = AdminToken.objects.create()
        
        # Return the token details
        return Response({
            "token": str(token.token),
            "name": token.name
        }, status=status.HTTP_201_CREATED)


class SendSingleNotificationView(APIView):
    """
    API view for sending a push notification to a single subscriber.
    
    Requires an admin token for authorization.
    Sends a web push notification to the provided subscription info.
    """
    def post(self, request):
        """
        POST method to send a notification to a single subscriber.
        
        Expected payload:
        {
            "admin_token": "uuid-string",
            "subscription_info": {
                "endpoint": "https://...",
                "keys": {
                    "p256dh": "base64-key",
                    "auth": "base64-auth"
                }
            },
            "title": "Notification Title",
            "body": "Notification Body",
            "icon": "icon-url",  # optional
            "url": "click-url"   # optional
        }
        
        Returns:
            Response: Success or error message
        """
        # Validate admin token
        admin_token = request.data.get("admin_token")
        if not admin_token:
            return Response({"admin_token": "required field"}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not AdminToken.objects.filter(token=admin_token).exists():
            return Response({"admin_token": "admin_token is invalid"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get notification details
        subscription_info = request.data.get("subscription_info")
        title = request.data.get('title')
        body = request.data.get("body")
        icon = request.data.get('icon', '')
        url = request.data.get("url", None)
        
        # Validate subscription info
        if not subscription_info:
            return Response({"subscription_info": "it's a required field"}, status=status.HTTP_400_BAD_REQUEST)

        # Prepare notification payload
        payload = json.dumps({
            "title": title,
            "body": body,
            "icon": icon,
            "url": url,
        })
        
        # Send the notification
        try:
            webpush(
                subscription_info,
                data=payload,
                vapid_private_key=config("VAPID_PRIVATE_KEY"),
                vapid_claims={"sub": config("VAPID_SUBJECT")}
            )
            
            return Response({"message": "notification sent successfully"}, status=status.HTTP_200_OK)
        except WebPushException as ex:
            return Response({"error": str(ex)}, status=status.HTTP_400_BAD_REQUEST)


class SendGroupNotificationView(APIView):
    """
    API view for sending push notifications to multiple subscribers.
    
    Requires an admin token for authorization.
    Sends the same notification to multiple subscription endpoints.
    Collects successes and failures for detailed response.
    """
    def post(self, request):
        """
        POST method to send notifications to multiple subscribers.
        
        Expected payload:
        {
            "admin_token": "uuid-string",
            "subscription_info_list": [
                {
                    "endpoint": "https://...",
                    "keys": { "p256dh": "...", "auth": "..." }
                },
                ...
            ],
            "title": "Notification Title",
            "body": "Notification Body",
            "icon": "icon-url",  # optional
            "url": "click-url"   # optional
        }
        
        Returns:
            Response: JSON with success and error lists
        """
        # Validate admin token
        admin_token = request.data.get("admin_token")
        if not admin_token:
            return Response({"admin_token": "required field"}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not AdminToken.objects.filter(token=admin_token).exists():
            return Response({"admin_token": "admin_token is invalid"}, status=status.HTTP_401_UNAUTHORIZED)

        # Get subscription list
        subscription_info_list = request.data.get("subscription_info_list")
        if not subscription_info_list or not isinstance(subscription_info_list, list):
            return Response(
                {"subscription_info_list": "It is a required field and also it's must be a list"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get notification details
        title = request.data.get("title")
        body = request.data.get("body")
        icon = request.data.get("icon", None)
        url = request.data.get("url", "")
        
        # Prepare notification payload
        payload = json.dumps({
            "title": title,
            "body": body,
            "icon": icon,
            "url": url,
        })
        
        # Track successful and failed notifications
        errors = []
        successes = []
        
        # Send notifications to each subscription
        for subscription_info in subscription_info_list:
            try:
                webpush(
                    subscription_info,
                    data=payload,
                    vapid_private_key=config("VAPID_PRIVATE_KEY"),
                    vapid_claims={"sub": config("VAPID_SUBJECT")}
                )
                successes.append(subscription_info['endpoint'])
            except WebPushException as ex:
                errors.append(subscription_info['endpoint'])
        
        # Return results
        return Response({
            'success': successes,
            "error": errors
        }, status=status.HTTP_200_OK)