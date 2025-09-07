from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from .models import CustomUser, KYC
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


# Register User
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'full_name', 'password', 'role']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(password=password, **validated_data)
        return user


# User Serializer for list/retrieve/update/delete
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

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


# Login Serializer
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            raise serializers.ValidationError("Must include email and password.")

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
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
        data["user"] = user

        return data


# KYC Serializer
class KYCSerializer(serializers.ModelSerializer):
    document_file = serializers.FileField(write_only=True)
    document_name = serializers.CharField(read_only=True)

    class Meta:
        model = KYC
        fields = ["document_type", "document_number", "document_file", "document_name"]

    def create(self, validated_data):
        file = validated_data.pop("document_file")
        validated_data["document_name"] = file.name
        validated_data["document_data"] = file.read()
        return super().create(validated_data)
