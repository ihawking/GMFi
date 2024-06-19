from rest_framework.permissions import BasePermission
from rest_framework.request import Request


class DenyAll(BasePermission):
    def has_permission(self, request: Request, view):
        return False

    def has_object_permission(self, request, view, obj):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return False
