from django.db import models
from django.contrib.auth import get_user_model
from courses.models import Course  
from django.core.files import File
from tempfile import NamedTemporaryFile
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

User = get_user_model()

def generate_user_key(user) -> bytes:
    secret = "my_global_secret"
    password = f"{user.id}-{secret}".encode()
    salt = f"user_salt_{user.id}".encode()
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return key

def encrypt_video_for_user(input_path: str, output_path: str, user):
    key = generate_user_key(user)
    fernet = Fernet(key)
    with open(input_path, "rb") as f:
        data = f.read()
    encrypted = fernet.encrypt(data)
    with open(output_path, "wb") as f:
        f.write(encrypted)

def lesson_video_upload_path(instance, filename):
    user_id = instance.created_by.id if instance.created_by else "anonymous"
    return f"videos/course_{instance.course.id}/lesson_{instance.id}/user_{user_id}/{filename}"

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    video_file = models.FileField(upload_to=lesson_video_upload_path, blank=True, null=True)
    order = models.PositiveIntegerField(default=1)
    is_published = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        unique_together = ("course", "order")

    def __str__(self):
        return f"{self.course.name} - {self.title}"

    def save(self, *args, **kwargs):
        if self.video_file and not self.video_file.name.endswith(".enc") and self.created_by:
            temp_file = NamedTemporaryFile(delete=False)
            encrypt_video_for_user(self.video_file.path, temp_file.name, self.created_by)

            with open(temp_file.name, "rb") as f:
                self.video_file.save(f"{self.video_file.name}.enc", File(f), save=False)
            os.remove(temp_file.name)

        super().save(*args, **kwargs)
