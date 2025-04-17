from rest_framework import serializers

class NotificationSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    body = serializers.CharField()
    token = serializers.CharField()
    
    def validate_token(self, value):
        if not value:
            raise serializers.ValidationError("Token is required for sending notifications.")
        return value