from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from .models import OTPRequest
from utils.utils import send_otp, validate_phone_number
from .models import normalize_phone_number
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import normalize_phone_number
import uuid


class UpdatePhoneNumberSerializer(serializers.Serializer):
    old_phone_number = serializers.CharField(max_length=20)
    new_phone_number = serializers.CharField(max_length=20)
    request_type = serializers.CharField(max_length=30)
    
    def validate_new_phone_number(self, value):
        normalize_new_number = normalize_phone_number(value)
        if get_user_model().objects.filter(phone_number = normalize_new_number).exists():
            raise serializers.ValidationError("This phone number is registered before")
        return normalize_new_number
    
    def validate_old_phone_number(self, value):
        normalize_old_number = normalize_phone_number(value)
        if get_user_model().objects.filter(phone_number = normalize_old_number).exists():
            return normalize_old_number
        raise serializers.ValidationError("user is not found")
    
    def validate_request_type(self, value):
        if not value in ['signup', 'password_reset', "phone_verification"]:
            raise serializers.ValidationError("request_type is wrong")
        return value
    
    def save(self):
        try:
            user = get_user_model().objects.filter(phone_number=self.validated_data.get("old_phone_number")).first()
            OTPRequest.objects.filter(phone_number = user.phone_number).delete()
            user.phone_number = self.validated_data.get("new_phone_number")
            user.is_active = False
            user.save()
            otp_request = OTPRequest.objects.create(phone_number=user.phone_number, request_type=self.validated_data.get("request_type"))
            return otp_request
        except:
            return {"error": "phone number is used before."}
    # def save(self):
        

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["email", "phone_number", "first_name", "last_name", "password"]
        
    def validate_phone_number(self, value):
        if normalize_phone_number(value):
            return normalize_phone_number(value)
        raise ValidationError({"error": "number is invalid."})

    def create(self, validated_data):
        user = get_user_model().objects.create(
            email = validated_data.get('email', None),
            first_name = validated_data.get('first_name'),
            last_name = validated_data.get('last_name'),
            phone_number = validated_data.get('phone_number'),
        )
        user.set_password(validated_data.get('password'))
        user.is_active = False
        user.save()
        otp = OTPRequest.objects.create(
            phone_number = user.phone_number,
            request_type = "signup"
        )
        
        send_otp(phone_number=user.phone_number, otp_code=otp.otp_code)
        return [user, otp]

class ResetPasswordSerializer(serializers.Serializer):
    register_id = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    
    def validate_register_id(self, value):
        if not value:
            return {"error": "register_id is required."}
    
        try:
            uuid.UUID(value)
        except ValueError:
            return {"error": "register_id is wrong."}
    
    def validate(self, data):
        otp_request = OTPRequest.objects.filter(register_id=data['register_id']).first()
        if otp_request and not otp_request.is_expired() and otp_request.request_type == 'password_reset' and otp_request.is_verified:
            user = get_user_model().objects.filter(phone_number=otp_request.phone_number).first()
            if user:
                user.set_password(data.get("new_password"))
                user.save()
                return data
        raise ValidationError("کد تایید اشتباه است یا منقضی شده است.")

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        user = self.context['request'].user
        if not user.check_password(data['old_password']):
            raise ValidationError("پسورد قبلی صحیح نیست.")
        return data

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data["new_password"])
        user.save()
    
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    
    def save(self):
        user = authenticate(username=self.validated_data.get('username', None), password=self.validated_data.get("password", None))
        if user:
            return user
        # raise ValidationError({"error": "username or password is incorrect"})

class ChangePhoneNumberSerializer(serializers.Serializer):
    new_phone_number = serializers.CharField()
    
    def create(self, validated_data):
        try:
            phone_number = normalize_phone_number(validated_data["new_phone_number"])
            if get_user_model().objects.filter(phone_number=phone_number).exists():
                raise serializers.ValidationError("the number is registered before.")
        except Exception as e:
            return {"error": "phone number is not valid"}
        
        user = self.context['request'].user
        user.phone_number = phone_number
        user.is_active = False
        user.save()
        otp_request = OTPRequest.objects.create(
            phone_number = phone_number,
            request_type = "phone_verification"
        )
        send_otp(user.phone_number, otp_request.otp_code)
        return {
            "message": "OTP just send.",
            "register_id": otp_request.register_id,
        }


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = [
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "is_superuser",
            "is_active",
        ]
        read_only_fields = ["phone_number", "email", 'is_superuser', 'is_active']