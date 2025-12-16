from rest_framework import permissions


#  Custom Permissions 
class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Admins can create/edit/delete.
    Regular users can only Read (GET).
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS: 
            return True
        return request.user and request.user.is_staff


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Used for Reviews.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user
