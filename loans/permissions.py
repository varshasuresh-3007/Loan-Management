from rest_framework.permissions import BasePermission

class IsAdminOrLoanOfficer(BasePermission):
    """
    ✅ Only admins and loan officers can access the view.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ["admin", "loan_officer"]


class IsLoanOwner(BasePermission):
    """
    ✅ Users can only access their own loans.
    ✅ Admins can access all loans.
    """
    def has_object_permission(self, request, view, obj):
        return request.user.role == "admin" or obj.user == request.user
