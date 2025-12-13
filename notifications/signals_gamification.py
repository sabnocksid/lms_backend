from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from notifications.models import Notification
from notifications.utils import send_realtime_notification

from gramafication.models import PointTransaction, CourseGamification
from gramafication.models import Enrollment
from courses.models import Course

User = get_user_model()
