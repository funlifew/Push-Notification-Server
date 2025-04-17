from django.shortcuts import render
from rest_framework import generics, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.views import Response, APIView
from utils.utils import send_web_push
from rest_framework.decorators import action
from .models import AdminToken
import json, random, string
from pywebpush import webpush, WebPushException
from decouple import config

# Create your views here.

class GenerateAdminTokenView(APIView):
    def post(self, request):
        
        token = AdminToken.objects.create()
        return Response({
            "token": str(token.token),
            "name": token.name
        }, status=status.HTTP_201_CREATED)

class SendSingleNotificationView(APIView):
    def post(self, request):
        admin_token = request.data.get("admin_token")
        if not admin_token:
            return Response({"admin_token": "required field"}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not AdminToken.objects.filter(token=admin_token).exists():
            return Response({"admin_token": "admin_token is invalid"})
        
        
        subscription_info = request.data.get("subscription_info")
        title = request.data.get('title')
        body = request.data.get("body")
        icon = request.data.get('icon', '')
        url = request.data.get("url", None)
        
        if not subscription_info:
            return Response({"subscription_info": "it's a required field"}, status=status.HTTP_400_BAD_REQUEST)

        payload = json.dumps({
            "title": title,
            "body": body,
            "icon": icon,
            "url": url,
        })
        
        try:
            response = webpush(
                subscription_info,
                data=payload,
                vapid_private_key=config("VAPID_PRIVATE_KEY"),
                vapid_claims={"sub": config("VAPID_SUBJECT")}
            )
            
            print(response)
            
            return Response({"message": "notification sent successfully"}, status=status.HTTP_200_OK)
        except WebPushException as ex:
            return Response({"error": str(ex)}, status=status.HTTP_400_BAD_REQUEST)

class SendGroupNotificationView(APIView):
    def post(self, request):
        admin_token = request.data.get("admin_token")
        if not admin_token:
            return Response({"admin_token": "required field"}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not AdminToken.objects.filter(token=admin_token).exists():
            return Response({"admin_token": "admin_token is invalid"})

        subscription_info_list = request.data.get("subscription_info_list")
        if not subscription_info_list or not isinstance(subscription_info_list, list):
            return Response({"subscription_info_list": "It is a required field and also it's must be a list"})

        title = request.data.get("title")
        body = request.data.get("body")
        icon = request.data.get("icon", None)
        url = request.data.get("url", "")
        
        payload = json.dumps({
            "title": title,
            "body": body,
            "icon": icon,
            "url": url,
        })
        
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
                successes.append(subscription_info['endpoint'])
            except WebPushException as ex:
                errors.append(subscription_info['endpoint'])
        
        return Response({
            'success': successes,
            "error": errors
        }, status=status.HTTP_200_OK)