from django.db.models import Avg, Q
from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, ChoiceFilter
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


class CourseFilter(FilterSet):
    RATING_CHOICES = [
        ('1', '1-2'),
        ('2', '2-3'),
        ('3', '3-4'),
        ('4', '4-5'),
        ('5', '5'),
    ]
    rating_range = ChoiceFilter(method='filter_rating_range', choices=RATING_CHOICES, label="Rating Range")

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

    def filter_rating_range(self, queryset, name, value):
        queryset = queryset.annotate(avg_rating=Avg('ratings__points'))

        if value == '1':
            return queryset.filter(avg_rating__gte=1, avg_rating__lt=2)
        elif value == '2':
            return queryset.filter(avg_rating__gte=2, avg_rating__lt=3)
        elif value == '3':
            return queryset.filter(avg_rating__gte=3, avg_rating__lt=4)
        elif value == '4':
            return queryset.filter(avg_rating__gte=4, avg_rating__lt=5)
        elif value == '5':
            return queryset.filter(avg_rating__gte=5)
        return queryset


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

from gramafication.algorithm.difficulty_predictor import predict_difficulty, get_recommendations


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    permission_classes = [IsInstructorOrAdminOrReadOnly]
    pagination_class = CoursePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CourseFilter
    search_fields = ["name", "description"]
    ordering_fields = ["date_added", "price", "avg_rating"]
    ordering = ["-date_added"]

    def get_queryset(self):
        return Course.objects.annotate(avg_rating=Avg("ratings__points")).order_by("-date_added")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CourseDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return CourseCreateUpdateSerializer
        return CoursePreviewSerializer

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


    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"success": True, "message": "Course deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )


    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


    @action(detail=True, methods=["get"], url_path="predict-difficulty")
    def predict_difficulty_view(self, request, pk=None):
        learner = getattr(request.user, "profile", None)
        if not learner:
            return Response({"detail": "Learner profile not found."}, status=status.HTTP_400_BAD_REQUEST)

        course = self.get_object()
        result = predict_difficulty(learner, course)
        return Response(result, status=status.HTTP_200_OK)


    @action(detail=False, methods=["get"], url_path="recommendations")
    def course_recommendations(self, request):
        learner = getattr(request.user, "profile", None)
        if not learner:
            return Response({"detail": "Learner profile not found."}, status=status.HTTP_400_BAD_REQUEST)

        max_level = int(request.query_params.get("max_level", 3))
        results = get_recommendations(learner, max_level=max_level)

        data = [
            {
                "course_id": r["course"].id,
                "name": r["course"].name,
                "difficulty": r["difficulty"],
                "success": r["success"],
                "days": r["days"],
            }
            for r in results
        ]

        return Response(data, status=status.HTTP_200_OK)

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
        avg_rating = course.ratings.aggregate(avg=Avg('points'))['avg'] or 0

        return Response(
            {
                "rating": serializer.data,
                "average_rating": avg_rating
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
