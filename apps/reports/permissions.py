"""
apps/reports/permissions.py

Rules:
- Only the nurse who did the visit can create/edit reports for it.
- Medical admin of the same hospital can review (approve/reject).
- Guardians can read reports for their dependent's visits.
- Approved reports are locked — no one can edit them.
"""

from rest_framework.permissions import BasePermission
from apps.hospitals.models import HospitalMembership
from apps.visits.models import VisitAssignment


class IsReportNurse(BasePermission):
    """
    Object-level permission.
    Only the nurse who was accepted for this visit can write reports.
    """
    message = "Only the assigned nurse can manage this report."

    def has_object_permission(self, request, view, obj):
        # obj is a Report instance
        return obj.nurse == request.user


class IsMedicalAdminOfHospital(BasePermission):
    """
    Checks the user is a medical admin of the hospital
    that owns this report's visit.
    """
    message = "Only a medical admin of this hospital can review reports."

    def has_object_permission(self, request, view, obj):
        return HospitalMembership.objects.filter(
            user=request.user,
            hospital=obj.visit.hospital,
            role=HospitalMembership.Role.MEDICAL_ADMIN,
            is_active=True,
        ).exists()