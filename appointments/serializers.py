from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Appointment

# **1. User Authentication Serializers**
class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['username', 'password']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = User.objects.filter(username=data['username']).first()
        if user and user.check_password(data['password']):
            refresh = RefreshToken.for_user(user)
            return {'refresh': str(refresh), 'access': str(refresh.access_token)}
        raise serializers.ValidationError("Invalid credentials")

# **2. Appointment Serializer**
class AppointmentSerializer(serializers.ModelSerializer):
    """Serializer for handling appointment data"""
    class Meta:
        model = Appointment
        fields = ['id', 'name', 'age', 'date','doctor', 'token_number', 'payment_id', 'payment_status']
        read_only_fields = ['token_number', 'payment_id', 'payment_status']
