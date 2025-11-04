from rest_framework import viewsets, permissions
from .models import DiscussionThread, DiscussionPost
from .serializers import DiscussionThreadSerializer, DiscussionPostSerializer

class DiscussionThreadViewSet(viewsets.ModelViewSet):
    queryset = DiscussionThread.objects.all()
    serializer_class = DiscussionThreadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        course_id = self.request.query_params.get("course")
        if course_id:
            return self.queryset.filter(course_id=course_id).order_by('-created_at')
        return self.queryset.all().order_by('-created_at')

class DiscussionPostViewSet(viewsets.ModelViewSet):
    queryset = DiscussionPost.objects.all()
    serializer_class = DiscussionPostSerializer
    permission_classes = [permissions.IsAuthenticated]




