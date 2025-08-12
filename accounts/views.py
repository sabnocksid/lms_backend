from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import GenericAPIView
from .models import CustomUser, KYC
from rest_framework.generics import ListAPIView

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    KYCSerializer,
    UserListSerializer
)
from .permissions import IsAdminCanApproveKYC
from rest_framework.permissions import IsAdminUser



class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(
                {"message": "User created successfully"},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
class LoginView(GenericAPIView):
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
        }, status=status.HTTP_200_OK)

class KYCSubmitView(generics.CreateAPIView):
    queryset = KYC.objects.all()
    serializer_class = KYCSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class PendingKYCUserListView(ListAPIView):
    serializer_class = UserListSerializer
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
    
class KYCDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            kyc = KYC.objects.get(pk=pk)
            response = HttpResponse(kyc.document_data, content_type="application/octet-stream")
            response['Content-Disposition'] = f'attachment; filename="{kyc.document_name}"'
            return response
        except KYC.DoesNotExist:
            return Response({"error": "KYC not found"}, status=404)


class UserListView(generics.ListAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserListSerializer