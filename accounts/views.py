from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.views import APIView
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

from .models import CustomUser, KYC
from .serializers import RegisterSerializer, UserSerializer, LoginSerializer, KYCSerializer



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

        kyc_verified = bool(getattr(user, "kyc", None) and user.kyc.approved_at)

        return Response({
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "kyc_verified": kyc_verified,
            "access": serializer.validated_data["access"],
            "refresh": serializer.validated_data["refresh"]
        }, status=status.HTTP_200_OK)



class UserPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

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

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "Deleted successfully"}, status=status.HTTP_200_OK)



class KYCSubmitView(generics.CreateAPIView):
    queryset = KYC.objects.all()
    serializer_class = KYCSerializer
    permission_classes = [IsAuthenticated]  

    def perform_create(self, serializer):
        serializer.save()


# Admin: View all KYC submissions
class KYCPageNumberPagination(PageNumberPagination):
    page_size = 10  
    page_size_query_param = 'page_size' 
    max_page_size = 100

class KYCListView(generics.ListAPIView):
    queryset = KYC.objects.all().order_by('-submitted_at')
    serializer_class = KYCSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = KYCPageNumberPagination 

class KYCApproveView(generics.UpdateAPIView):
    queryset = KYC.objects.all()
    serializer_class = KYCSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, *args, **kwargs):
        kyc = self.get_object()
        if kyc.approved_at:
            return Response({"detail": "Already approved"}, status=status.HTTP_400_BAD_REQUEST)

        kyc.approved_at = timezone.now()
        kyc.save()

        user = kyc.user
        user.kyc_verified = True
        user.save()

        return Response({"detail": f"KYC for {user.email} approved successfully"}, status=status.HTTP_200_OK)


# Approve KYC (Admin)
class KYCApproveView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, pk):
        try:
            kyc = KYC.objects.get(pk=pk)
        except KYC.DoesNotExist:
            return Response({"error": "KYC not found"}, status=status.HTTP_404_NOT_FOUND)
        
        kyc.approved_at = timezone.now()
        kyc.save()
        
        user = kyc.user
        user.kyc_verified = True
        user.save()
        
        return Response({"message": f"KYC for {user.email} approved."}, status=status.HTTP_200_OK)

# Retrieve KYC Status (User)
class KYCStatusView(RetrieveAPIView):
    serializer_class = KYCSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return KYC.objects.get(user=self.request.user)
