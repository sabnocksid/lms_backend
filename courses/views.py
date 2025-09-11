from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Category, Course, Rating
from .serializers import (
    CategorySerializer,
    CoursePreviewSerializer,
    CourseDetailSerializer,
    CourseCreateUpdateSerializer,
    RatingSerializer
)
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
    filterset_fields = ["categories", "is_published", "instructor"]  
    search_fields = ["name", "description"]
    ordering_fields = ["date_added", "rating", "price"]
    ordering = ["-date_added"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CourseDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return CourseCreateUpdateSerializer
        return CoursePreviewSerializer



class CourseRatingViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=["POST"])
    def rate(self, request, pk=None):
        course = Course.objects.get(pk=pk)
        points = request.data.get("points")

        if points is None:
            return Response({"error": "Rating points required"}, status=status.HTTP_400_BAD_REQUEST)

        rating_obj, created = Rating.objects.update_or_create(
            user=request.user,
            course=course,
            defaults={"points": points},
        )

        serializer = RatingSerializer(rating_obj)
        return Response(serializer.data, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)