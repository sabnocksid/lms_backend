from rest_framework import viewsets, permissions
from .models import DiscussionThread, DiscussionPost
from .serializers import DiscussionThreadSerializer, DiscussionPostSerializer
from gramafication.models import Enrollment

class DiscussionThreadViewSet(viewsets.ModelViewSet):
    queryset = DiscussionThread.objects.all().order_by('-created_at')
    serializer_class = DiscussionThreadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.is_staff or user.is_superuser:
            return self.queryset.select_related("course", "course__instructor")

        if hasattr(user, "profile"):
            enrolled_courses = Enrollment.objects.filter(
                learner=user.profile,
                is_active=True
            ).values_list("course_id", flat=True)
            return self.queryset.filter(
                course_id__in=enrolled_courses
            ).select_related("course", "course__instructor")

        return self.queryset.filter(
            course__instructor=user
        ).select_related("course", "course__instructor")

class DiscussionPostViewSet(viewsets.ModelViewSet):
    queryset = DiscussionPost.objects.all()
    serializer_class = DiscussionPostSerializer
    permission_classes = [permissions.IsAuthenticated]




