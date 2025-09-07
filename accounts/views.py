from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.utils.timezone import now
from django.http import HttpResponse
from .models import CustomUser, KYC
from .serializers import RegisterSerializer, LoginSerializer, KYCSerializer, UserSerializer
from .permissions import IsAdminCanApproveKYC

# -----------------------------
# Existing Views (Register, Login, KYC)
# -----------------------------
class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        return Response({
            "message": "Login successful",
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "access": serializer.validated_data["access"],
            "refresh": serializer.validated_data["refresh"]
        })


class KYCSubmitView(generics.CreateAPIView):
    queryset = KYC.objects.all()
    serializer_class = KYCSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PendingKYCUserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return CustomUser.objects.filter(kyc_verified=False)


class KYCApproveView(generics.UpdateAPIView):
    queryset = KYC.objects.all()
    serializer_class = KYCSerializer
    permission_classes = [IsAdminCanApproveKYC]

    def update(self, request, *args, **kwargs):
        kyc = self.get_object()
        kyc.user.kyc_verified = True
        kyc.user.is_active = True
        kyc.approved_at = now()
        kyc.user.save()
        kyc.save()
        return Response({"status": "KYC Approved"})


class KYCDownloadView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            kyc = KYC.objects.get(pk=pk)
            response = HttpResponse(kyc.document_data, content_type="application/octet-stream")
            response['Content-Disposition'] = f'attachment; filename="{kyc.document_name}"'
            return response
        except KYC.DoesNotExist:
            return Response({"error": "KYC not found"}, status=404)

# -----------------------------
# User CRUD Views
# -----------------------------

class UserListView(generics.ListAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class UserRetrieveView(generics.RetrieveAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class UserUpdateView(generics.UpdateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class UserPartialUpdateView(generics.UpdateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class UserDeleteView(generics.DestroyAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()
