from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.generics import RetrieveUpdateDestroyAPIView, GenericAPIView
from rest_framework.pagination import PageNumberPagination

from .models import CustomUser
from .serializers import RegisterSerializer, UserSerializer, LoginSerializer

# Register
class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

# Login
class LoginView(GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        return Response({
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "access": serializer.validated_data["access"],
            "refresh": serializer.validated_data["refresh"]
        }, status=status.HTTP_200_OK)

# Pagination for users
class UserPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

# List Users (Admin Only)
class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = UserPagination

    def get_queryset(self):
        queryset = CustomUser.objects.all().order_by("-id")
        role = self.request.query_params.get("role")
        search = self.request.query_params.get("search")

        if role:
            queryset = queryset.filter(role__iexact=role)
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) | Q(email__icontains=search)
            )
        return queryset

# User Detail (Admin Only)
class UserDetailView(RetrieveUpdateDestroyAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "Deleted successfully"}, status=status.HTTP_200_OK)
