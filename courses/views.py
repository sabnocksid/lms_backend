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
from gramafication.algorithm.difficulty_predictor import predict_difficulty

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class CourseFilter(FilterSet):
    RATING_CHOICES = [
        ('1', '1-2'),
        ('2', '2-3'),
        ('3', '3-4'),
        ('4', '4-5'),
        ('5', '5'),
    ]

    DIFFICULTY_CHOICES = [
        ('1', 'Very Easy'),
        ('2', 'Easy'),
        ('3', 'Moderate'),
        ('4', 'Challenging'),
        ('5', 'Very Challenging'),
    ]

    rating_range = ChoiceFilter(method='filter_rating_range', choices=RATING_CHOICES, label="Rating Range")
    difficulty_level = ChoiceFilter(method='filter_difficulty_level', choices=DIFFICULTY_CHOICES, label="Difficulty Level")

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

    def filter_difficulty_level(self, queryset, name, value):
        learner = getattr(self.request.user, "profile", None)
        if not learner:
            return queryset.none()

        filtered_ids = []
        for course in queryset:
            try:
                prediction = predict_difficulty(learner, course)
                if str(prediction["level"]) == value:
                    filtered_ids.append(course.id)
            except Exception:
                continue

        return queryset.filter(id__in=filtered_ids)

from gramafication.models import Enrollment


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

    def _get_learner_progress(self, learner, course):
        enrollment = Enrollment.objects.filter(learner=learner, course=course).first()
        if enrollment and hasattr(enrollment, "gamification"):
            g = enrollment.gamification

            # Use try/except to avoid any missing attribute errors
            try:
                completed_chapters = ChapterProgress.objects.filter(
                    user=learner.user,
                    chapter__lesson__course=course,
                    completed=True
                ).count()

                attempted_quizzes = QuizAttempt.objects.filter(
                    user=learner.user,
                    quiz__course=course
                ).count()

                total_chapters = Chapter.objects.filter(lesson__course=course).count()
                total_quizzes = Quiz.objects.filter(course=course).count()

                completed = (completed_chapters >= total_chapters if total_chapters else True) and \
                            (attempted_quizzes >= total_quizzes if total_quizzes else True)

                progress_percent = int(
                    ((completed_chapters / total_chapters) * 50 if total_chapters else 50) +
                    ((attempted_quizzes / total_quizzes) * 50 if total_quizzes else 50)
                )

                return {
                    "chapters_completed": completed_chapters,
                    "total_chapters": total_chapters,
                    "quizzes_attempted": attempted_quizzes,
                    "total_quizzes": total_quizzes,
                    "progress_percent": progress_percent,
                    "completed": completed,
                }

            except Exception:
                return None

        return None


    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        learner = getattr(request.user, "profile", None)
        data = serializer.data

        if learner:
            for i, course_data in enumerate(data):
                course_instance = page[i]

                try:
                    prediction = predict_difficulty(learner, course_instance)
                    course_data["difficulty"] = prediction
                except Exception as e:
                    print(f"Predict difficulty failed for course {course_instance.id}: {e}")
                    course_data["difficulty"] = {
                        "level": 0,
                        "name": "Unknown",
                        "skill": 0,
                        "difficulty": 0,
                        "gap": 0,
                        "success": 0,
                        "days": 0,
                        "recommendation": "N/A"
                    }

                course_data["learner_progress"] = self._get_learner_progress(learner, course_instance)

        return self.get_paginated_response(data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        learner = getattr(request.user, "profile", None)

        data["learner_progress"] = None
        data["difficulty"] = None

        if learner:
            try:
                prediction = predict_difficulty(learner, instance)
                data["difficulty"] = prediction
            except Exception:
                data["difficulty"] = None

            data["learner_progress"] = self._get_learner_progress(learner, instance)

        return Response(data, status=status.HTTP_200_OK)

    # @action(detail=False, methods=["get"], url_path="recommendations")
    # def course_recommendations(self, request):
    #     learner = getattr(request.user, "profile", None)
    #     if not learner:
    #         return Response({"detail": "Learner profile not found."}, status=status.HTTP_400_BAD_REQUEST)

    #     max_level = int(request.query_params.get("max_level", 3))
    #     results = get_recommendations(learner, max_level=max_level)

    #     data = [
    #         {
    #             "course_id": r["course"].id,
    #             "name": r["course"].name,
    #             "difficulty": r["difficulty"],
    #             "success": r["success"],
    #             "days": r["days"],
    #         }
    #         for r in results
    #     ]
    #     return Response(data, status=status.HTTP_200_OK)

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
