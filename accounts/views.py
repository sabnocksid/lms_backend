from rest_framework import generics, status
from rest_framework.response import Response
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.generics import RetrieveUpdateDestroyAPIView, GenericAPIView
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework import viewsets
from .models import CustomUser
from django.db.models import Q
from .serializers import RegisterSerializer, UserSerializer, LoginSerializer, UserRoleSerializer, AdminUserCreateSerializer

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


class VerifyEmailView(APIView):
    permission_classes = [AllowAny] 

    def get(self, request):
        token = request.query_params.get('token')
        if not token:
            return Response({"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)

        signer = TimestampSigner()
        try:
            user_id = signer.unsign(token, max_age=60*60*24)  
            user = CustomUser.objects.get(pk=user_id)
            user.is_active = True
            user.save()
            return Response({"message": "Email verified successfully!"}, status=status.HTTP_200_OK)

        except SignatureExpired:
            return Response({"error": "Verification link expired."}, status=status.HTTP_400_BAD_REQUEST)

        except (BadSignature, CustomUser.DoesNotExist):
            return Response({"error": "Invalid verification token."}, status=status.HTTP_400_BAD_REQUEST)
        


class UserRoleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserRoleSerializer
    queryset = CustomUser.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        return queryset
    


class AdminUserCreateView(generics.CreateAPIView):
    serializer_class = AdminUserCreateSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = CustomUser.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        role = serializer.validated_data.get("role")
        
        extra_fields = {}
        if role == "admin":
            extra_fields["is_staff"] = True
            extra_fields["is_active"] = True
        
        user = serializer.save(**extra_fields)
        
        return Response({
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active
        }, status=status.HTTP_201_CREATED)
    

from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist

class UserUpdateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')
        
        try:
            instance = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        user = request.user
        
        if instance.role == 'student':
            if user != instance:
                if 'is_active' in request.data:
                    instance.is_active = not instance.is_active
                else:
                    return Response(
                        {"detail": "Only 'is_active' field can be updated for students."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                if user.role != 'admin':
                    return Response(
                        {"detail": "Admin privileges required to update student profiles."},
                        status=status.HTTP_403_FORBIDDEN
                    )

        elif instance.role == 'instructor':
            if user != instance and user.role != 'admin':  
                return Response(
                    {"detail": "Only instructors can update their own name and email."},
                    status=status.HTTP_403_FORBIDDEN
                )

            if user.role == 'admin':
                allowed_fields = ['full_name', 'email', 'role', 'is_active']
            else:
                allowed_fields = ['full_name', 'email', 'is_active']

            filtered_data = {key: value for key, value in request.data.items() if key in allowed_fields}
            
            if len(filtered_data) != len(request.data):
                return Response(
                    {"detail": "Only 'full_name', 'email', 'role', and 'is_active' can be updated for instructors."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            request_data = filtered_data

        elif instance.role == 'admin':
            if user != instance and user.role != 'admin':  
                return Response(
                    {"detail": "Only admins can update admin profiles."},
                    status=status.HTTP_403_FORBIDDEN
                )

            allowed_fields = ['full_name', 'email', 'password', 'is_active', 'role']
            filtered_data = {key: value for key, value in request.data.items() if key in allowed_fields}
            
            if len(filtered_data) != len(request.data):
                return Response(
                    {"detail": "Only 'full_name', 'email', 'password', 'is_active', and 'role' can be updated for admins."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            request_data = filtered_data

        if 'password' in request.data:
            password = request.data.get('password')
            if password:
                instance.set_password(password)

        serializer = UserSerializer(instance, data=request_data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



from django.contrib.auth import logout
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(["POST"])
def logout_view(request):
    logout(request)
    return Response({"detail": "Logged out successfully"})