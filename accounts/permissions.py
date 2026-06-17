from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):

    def has_permission(self, request, view):
        return request.user.role == "ADMIN"
class IsManager(BasePermission):

    def has_permission(self, request, view):
        return request.user.role == "MANAGER"