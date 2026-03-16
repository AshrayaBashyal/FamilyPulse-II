"""
Hospital admin analytics endpoints.
"""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from apps.hospitals.models import HospitalMembership
from apps.analytics.services import hospitaladmin_analytics
from .utils import parse_date_params, parse_group_by, require_hospital_role


class HospitalVisitSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Hospital visit summary (hospital admin)", tags=["Analytics-Hospitaladmin"])
    def get(self, request, hospital_id):
        hospital, error = require_hospital_role(
            request.user, hospital_id,
            roles=[HospitalMembership.Role.HOSPITAL_ADMIN],
        )
        if error:
            return error

        date_from, date_to = parse_date_params(request)
        data = hospitaladmin_analytics.hospital_visit_summary(hospital, date_from, date_to)
        return Response(data)


class HospitalVisitsOverTimeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Hospital visits over time (hospital admin)", tags=["Analytics-Hospitaladmin"])
    def get(self, request, hospital_id):
        hospital, error = require_hospital_role(
            request.user, hospital_id,
            roles=[HospitalMembership.Role.HOSPITAL_ADMIN],
        )
        if error:
            return error

        date_from, date_to = parse_date_params(request)
        group_by = parse_group_by(request, default="day")
        data = hospitaladmin_analytics.hospital_visits_over_time(hospital, date_from, date_to, group_by)
        return Response(data)


class HospitalReportSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Hospital report summary (hospital/medical admin)", tags=["Analytics-Hospitaladmin"])
    def get(self, request, hospital_id):
        hospital, error = require_hospital_role(
            request.user, hospital_id,
            roles=[
                HospitalMembership.Role.HOSPITAL_ADMIN,
                HospitalMembership.Role.MEDICAL_ADMIN,
            ],
        )
        if error:
            return error

        date_from, date_to = parse_date_params(request)
        data = hospitaladmin_analytics.hospital_report_summary(hospital, date_from, date_to)
        return Response(data)


class HospitalNurseSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Per-nurse breakdown (hospital admin)", tags=["Analytics-Hospitaladmin"])
    def get(self, request, hospital_id):
        hospital, error = require_hospital_role(
            request.user, hospital_id,
            roles=[HospitalMembership.Role.HOSPITAL_ADMIN],
        )
        if error:
            return error

        date_from, date_to = parse_date_params(request)
        data = hospitaladmin_analytics.hospital_nurse_summary(hospital, date_from, date_to)
        return Response(data)