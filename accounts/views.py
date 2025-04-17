from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status, generics
from django.contrib.auth import get_user_model
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    ResetPasswordSerializer,
    ChangePasswordSerializer,
    ChangePhoneNumberSerializer,
    ProfileSerializer,
    UpdatePhoneNumberSerializer,
)
from .models import OTPRequest, normalize_phone_number
from utils.utils import send_otp, validate_phone_number
from django.utils import timezone
from datetime import timedelta
import uuid
# Create your views here.

User = get_user_model()

def check_register_id(register_id=None):
    if not register_id:
        return Response({"error": "register_id is required."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        uuid.UUID(register_id)
    except ValueError:
        return Response({"error": "register_id is wrong."}, status=status.HTTP_400_BAD_REQUEST)
    
    return register_id

class EditPhoneNumberView(generics.GenericAPIView):
    serializer_class = UpdatePhoneNumberSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        otp = serializer.save()
        send_otp(otp.phone_number, otp.otp_code)
        return Response({
            "message": "phone number has changed successfully",
            "register_id": otp.register_id,
            "request_type": otp.request_type,
            "phone_number": otp.phone_number,
        })

class RegisterView(generics.GenericAPIView):
    serializer_class = RegisterSerializer
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            datas = serializer.save()
            user = datas[0]
            otp = datas[1]
            return Response({
                "message": "User registered. Please Verify OTP.",
                "register_id": otp.register_id,
                "old_phone_number": user.phone_number,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        if not user.is_active:
            otp_request = OTPRequest.objects.create(
                phone_number = user.phone_number,
                request_type='signup'
            )
            send_otp(user.phone_number, otp_request.otp_code)
            return Response({"message": "OTP sent for activation."}, status=status.HTTP_400_BAD_REQUEST)
        
        refresh = RefreshToken.for_user(user)
        response = Response({
            "access_token": str(refresh.access_token),
        })
        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            samesite='Lax'
        )
        return response

class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        response = Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
        response.delete_cookie('refresh_token')
        return response
    
class CustomTokenRefreshView(APIView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            return Response({"error": "No refresh token in"}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
            return Response({"access_token": access_token}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED)

class ChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)

class ChangePhoneNumberView(generics.GenericAPIView):
    serializer_class = ChangePhoneNumberSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "OTP sent to new phone number."})


class ProfileView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer
    
    def get(self, request, *args, **kwargs):
        user = request.user
        return Response({
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone_number": user.phone_number,
            "email": user.email,
            "is_superuser": user.is_superuser,
            "is_active": user.is_active
        }, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(instance=request.user, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            

class ResetPasswordRequestView(APIView):
    def post(self, request):
        phone_number = request.data['phone_number']
        # if phone number is doesn't exists we're going to send an error
        if not phone_number:
            return Response({"error": "Phone number is a required field."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate phone_number
        phone_number = validate_phone_number(phone_number)
        # normalize phone_number
        try:
            phone_number = normalize_phone_number(phone_number)
        except:
            return Response({"error": "invalid phone number."}, status=status.HTTP_400_BAD_REQUEST)
        
        # check for user is exsisting or not
        if User.objects.filter(phone_number=phone_number).first():
            # creating an otp code for user
            otp_request = OTPRequest.objects.create(
                phone_number = phone_number,
                request_type = 'reset_password'
            )
            # sending the otp via SMS
            send_otp(phone_number, otp_request.otp_code)
            return Response({"message": "OTP request just sent."}, status=status.HTTP_200_OK)
        return Response({"error": "use doesn't exists"}, status=status.HTTP_404_NOT_FOUND)

class ResetPasswordVerifyView(APIView):
    def post(self, request):
        register_id = request.data.get("register_id", None)
        otp_code = request.data.get("otp_code", None)
        
        if not register_id:
            return Response({"error": "register_id is required"}, status=status.HTTP_401_UNAUTHORIZED)
        if not otp_code:
            return Response({"error": "otp_code is required."}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            uuid.UUID(register_id)
        except:
            return Response({"error": "register_id is invalid"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            otp_request = OTPRequest.objects.filter(register_id=register_id, otp_code=otp_code, request_type="password_reset").first()
        except OTPRequest.DoesNotExist:
            return Response({"error": "otp_code is invalid."}, status=status.HTTP_400_BAD_REQUEST)
        
        otp_request.is_verified = True
        otp_request.save()
        return Response({"message": "otp is verified you are able to reset your password"}, status=status.HTTP_200_OK)
        
        

class ResetPasswordView(generics.GenericAPIView):
    serializers = ResetPasswordSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyOTPView(APIView):
    def post(self, request):
        register_id = request.data.get("register_id")
        otp_code = request.data.get('otp_code')
        
        check_register_id(register_id)
        
        if not otp_code:
            return Response({"error": "otp_code is a required field"})
        
        try:
            otp_request = OTPRequest.objects.filter(register_id=register_id, otp_code=otp_code, is_verified=False).first()
            print(register_id)
        except OTPRequest.DoesNotExist:
            return Response({"error": "otp is does not exists."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not otp_request.is_expired():
            print("user is here but i've got some fuckin problems")
            user = User.objects.filter(phone_number = otp_request.phone_number).first()
            user.is_active = True
            print(user.phone_number)
            otp_request.is_verified = True
            user.save()
            otp_request.save()
            refresh = RefreshToken.for_user(user)
            
            response =  Response({"message": "your account has been verified.", 'access_token': str(refresh.access_token)}, status=status.HTTP_200_OK)
            print("problem is here...")
            response.set_cookie(
                key="refresh_token",
                value=str(refresh),
                httponly=True,
                samesite='Lax'
            )
            return response
        print(otp_request.is_expired())
        return Response({"error": "your code had been expired."}, status=status.HTTP_400_BAD_REQUEST)
        

class RefreshTokenView(APIView):
    def post(self, request):
        register_id = request.data.get("register_id")
        print(check_register_id(register_id))
        
        try:
            otp_request = OTPRequest.objects.filter(register_id=register_id).first()
        except OTPRequest.DoesNotExist:
            return Response({"error": "otp is does not exists."}, status=status.HTTP_400_BAD_REQUEST)

        if otp_request.is_refreshable():
            otp_request.is_verified = False
            otp_request.otp_code = otp_request.generate_otp()
            otp_request.expires_at = timezone.now() + timedelta(minutes=5)
            otp_request.refreshes_at = timezone.now() + timedelta(minutes=2)
            otp_request.is_verified = False
            otp_request.save()
            send_otp(otp_request.phone_number, otp_request.otp_code)
            return Response({"message": "new otp generated.", "register_id": register_id}, status=status.HTTP_200_OK)

        return Response({"error": "you have to wait 2 minutes"}, status=status.HTTP_400_BAD_REQUEST)