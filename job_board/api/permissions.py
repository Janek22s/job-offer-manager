from rest_framework.permissions import BasePermission

class IsCandidate(BasePermission):
    message = "Access for candidates only."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "Candidate"
        )


class IsEmployer(BasePermission):
    message = "Access for employers only."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "Employer"
        )


class IsAdmin(BasePermission):
    message = "Access for admins only."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                request.user.role == "Admin"
                or request.user.is_staff
                or request.user.is_superuser
            )
        )