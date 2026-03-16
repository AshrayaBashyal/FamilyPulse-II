"""
Medical admin review analytics.
"""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from apps.hospitals.models import HospitalMembership
from apps.analytics.services import medicaladmin_analytics
from .utils import parse_date_params, require_hospital_role


class MedicalAdminReviewSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Report review summary (medical admin)", tags=["Analytics-Medicaladmin"])
    def get(self, request, hospital_id):
        hospital, error = require_hospital_role(
            request.user, hospital_id,
            roles=[
                HospitalMembership.Role.MEDICAL_ADMIN,
                HospitalMembership.Role.HOSPITAL_ADMIN,
            ],
        )
        if error:
            return error

        date_from, date_to = parse_date_params(request)

        # Optional: filter to only this admin's own reviews
        own_only = request.query_params.get("own_only", "false").lower() == "true"
        reviewed_by = request.user if own_only else None

        data = medicaladmin_analytics.medical_admin_review_summary(
            hospital, reviewed_by=reviewed_by,
            date_from=date_from, date_to=date_to,
        )
        return Response(data)