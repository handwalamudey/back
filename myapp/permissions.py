from rest_framework import permissions

class IsAdminOrAspirant(permissions.BasePermission):
    """
    Allows access only to Admin or Aspirant roles.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in ['admin', 'aspirant'])

class IsStaff(permissions.BasePermission):
    """
    Allows access only to Staff role.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'staff')

class RoleBasedPermission(permissions.BasePermission):
    """
    Custom permission to handle access based on roles.
    - Admin/Aspirant: Full Access
    - Staff: Limited access (e.g., Read Only on some resources)
    """
    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        # Special-case: allow Noordin full access (including bulk upload)
        if getattr(user, "username", "").lower() == "noordin":
            return True
        
        if user.role in ['admin', 'aspirant']:
            return True
            
        if user.role == 'staff':
            # Staff might only have GET permissions for certain views
            if request.method in permissions.SAFE_METHODS:
                return True
            return False
            
        return False
