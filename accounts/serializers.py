from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from .models import CustomUser, KYC
from rest_framework_simplejwt.tokens import RefreshToken
import base64
from django.conf import settings


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = CustomUser
        fields = ['email', 'full_name', 'password', 'role']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(password=password, **validated_data)
        return user



class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=6)

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'full_name', 'role', 'is_active', 'kyc_verified', 'password']
        read_only_fields = ['id', 'kyc_verified']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = CustomUser(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance



class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    role = serializers.CharField(read_only=True)
    kyc_verified = serializers.SerializerMethodField(read_only=True)

    def get_kyc_verified(self, obj):
        user = obj
        return hasattr(user, 'kyc') and user.kyc.approved_at is not None

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            raise serializers.ValidationError("Must include email and password.")

        try:
            user_obj = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")

        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password
        )

        if not user:
            raise serializers.ValidationError("Incorrect password.")

        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")

        refresh = RefreshToken.for_user(user)
        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)
        data["full_name"] = user.full_name
        data["role"] = user.role
        data["kyc_verified"] = hasattr(user, 'kyc') and user.kyc.approved_at is not None
        data["user"] = user
        return data





class SimpleUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    full_name = serializers.CharField()
    role = serializers.CharField()

class KYCSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)
    document_file = serializers.FileField(write_only=True)
    document_name = serializers.CharField(read_only=True)
    document_url = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    approved_at = serializers.DateTimeField(read_only=True)
    submitted_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = KYC
        fields = [
            "id",
            "user",
            "document_type",
            "document_number",
            "document_file",
            "document_name",
            "document_url",
            "status",
            "approved_at",
            "submitted_at"
        ]

    def get_status(self, obj):
        return "Approved" if obj.approved_at else "Pending"

    def get_document_url(self, obj):
        if obj.document_file:
            return obj.document_file.url  
        return None

    def create(self, validated_data):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required to submit KYC.")

        if KYC.objects.filter(user=request.user).exists():
            raise serializers.ValidationError("You have already submitted KYC.")

        file = validated_data.pop("document_file")
        validated_data["user"] = request.user
        validated_data["document_name"] = file.name
        validated_data["document_file"] = file  

        return super().create(validated_data)
