from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Course
from .serializers import CategorySerializer, CoursePreviewSerializer, CourseDetailSerializer
from .permissions import IsAdminOrReadOnly, IsInstructorOrAdminOrReadOnly
from .pagination import CoursePagination


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().order_by("-date_added")
    permission_classes = [IsInstructorOrAdminOrReadOnly]
    pagination_class = CoursePagination

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "is_published", "instructor"]
    search_fields = ["name", "description"]
    ordering_fields = ["date_added", "rating", "price"]
    ordering = ["-date_added"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CourseDetailSerializer  
        return CoursePreviewSerializer 
