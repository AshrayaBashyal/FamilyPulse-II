from rest_framework.permissions import BasePermission
from apps.dependents.models import Guardianship


class IsGuardian(BasePermission):
    message = "You must be a guardian of this dependent to perform this action."

    def has_object_permission(self, request, view, obj):
        # obj here is a Dependent instance
        return Guardianship.objects.filter(
            user=request.user,
            dependent=obj,
            is_active=True,
        ).exists()