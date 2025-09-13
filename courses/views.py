from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, NumberFilter
from rest_framework import viewsets, permissions, status, filters
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



# Custom FilterSet to include average_rating
class CourseFilter(FilterSet):
    min_rating = NumberFilter(method='filter_min_rating', label='Min Rating')
    max_rating = NumberFilter(method='filter_max_rating', label='Max Rating')

    class Meta:
        model = Course
        fields = {
            "categories": ["exact", "in"],
            "is_published": ["exact"],
            "instructor": ["exact"],
            "price": ["exact", "gte", "lte"],
            "date_added": ["exact", "gte", "lte"],
            "duration": ["exact", "gte", "lte"],
        }

    def filter_min_rating(self, queryset, name, value):
        return queryset.annotate(avg_rating=Avg('ratings__points')).filter(avg_rating__gte=value)

    def filter_max_rating(self, queryset, name, value):
        return queryset.annotate(avg_rating=Avg('ratings__points')).filter(avg_rating__lte=value)


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().order_by("-date_added")
    permission_classes = [IsInstructorOrAdminOrReadOnly]
    pagination_class = CoursePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CourseFilter

    search_fields = ["name", "description"]
    ordering_fields = ["date_added", "price", "avg_rating"]
    ordering = ["-date_added"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CourseDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return CourseCreateUpdateSerializer
        return CoursePreviewSerializer

    # Create
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Course creation failed", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"success": True, "message": "Course created successfully", "data": serializer.data},
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    # Update
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Course update failed", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.perform_update(serializer)
        return Response(
            {"success": True, "message": "Course updated successfully", "data": serializer.data},
            status=status.HTTP_200_OK,
        )

    # Delete
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"success": True, "message": "Course deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )



class CourseRatingViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=["POST"])
    def rate(self, request, pk=None):
        try:
            course = Course.objects.get(pk=pk)
        except Course.DoesNotExist:
            return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)

        points = request.data.get("points")
        try:
            points = int(points)
            if points < 0 or points > 5:
                raise ValueError()
        except (TypeError, ValueError):
            return Response(
                {"error": "Points must be an integer between 0 and 5"},
                status=status.HTTP_400_BAD_REQUEST
            )

        rating_obj, created = Rating.objects.update_or_create(
            user=request.user,
            course=course,
            defaults={"points": points},
        )

        serializer = RatingSerializer(rating_obj, context={"request": request})
        avg_rating = course.average_rating

        return Response(
            {
                "rating": serializer.data,
                "average_rating": avg_rating
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )