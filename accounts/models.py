import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

ROLE_CHOICES = (
    ('admin', 'Admin'),
    ('instructor', 'Instructor'),
    ('student', 'Student'),
)

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        if not user.encryption_key:
            user.encryption_key = uuid.uuid4().hex  
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    full_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=False)  
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    encryption_key = models.CharField(max_length=64, editable=False)
    kyc_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'role']

    objects = CustomUserManager()

    def __str__(self):
        return self.email


class KYC(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="kyc")
    document_type = models.CharField(max_length=50)
    document_number = models.CharField(max_length=100)
    
    document_name = models.CharField(max_length=255)  
    document_data = models.BinaryField()  
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"KYC for {self.user.email}"
