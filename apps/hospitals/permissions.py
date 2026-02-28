"""
How DRF permissions work:
- has_permission(request, view) -> called on every request before the view runs
- has_object_permission(request, view, obj) -> called when you do get_object()
- Return True = allow, False = 403 Forbidden

The hospital is identified from the URL kwargs (hospital_id).
"""

from rest_framework.permissions import BasePermission
from apps.hospitals.models import HospitalMembership


def get_user_membership(user, hospital_id):
    return HospitalMembership.objects.filter(
        user=user,
        hospital_id=hospital_id,
        is_active=True,
    ).first()


class IsHospitalAdmin(BasePermission):
    message = "You must be a Hospital Admin to perform this action."

    def has_permission(self, request, view):
        hospital_id = view.kwargs.get("hospital_id")
        if not hospital_id:
            return False
        membership = get_user_membership(request.user, hospital_id)
        return membership is not None and membership.role == HospitalMembership.Role.HOSPITAL_ADMIN


class IsMedicalAdmin(BasePermission):
    message = "You must be a Medical Admin to perform this action."

    def has_permission(self, request, view):
        hospital_id = view.kwargs.get("hospital_id")
        if not hospital_id:
            return False
        membership = get_user_membership(request.user, hospital_id)
        return membership is not None and membership.role == HospitalMembership.Role.MEDICAL_ADMIN


class IsHospitalAdminOrMedicalAdmin(BasePermission):
    message = "You must be a Hospital Admin or Medical Admin."

    def has_permission(self, request, view):
        hospital_id = view.kwargs.get("hospital_id")
        if not hospital_id:
            return False
        membership = get_user_membership(request.user, hospital_id)
        return membership is not None and membership.role in [
            HospitalMembership.Role.HOSPITAL_ADMIN,
            HospitalMembership.Role.MEDICAL_ADMIN,
        ]


class IsHospitalMember(BasePermission):
    message = "You must be a member of this hospital."

    def has_permission(self, request, view):
        hospital_id = view.kwargs.get("hospital_id")
        if not hospital_id:
            return False
        membership = get_user_membership(request.user, hospital_id)
        return membership is not None