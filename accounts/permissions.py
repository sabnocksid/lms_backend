from rest_framework.permissions import BasePermission

class IsAdminCanApproveKYC(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

class IsStudentOrInstructor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['student', 'instructor']