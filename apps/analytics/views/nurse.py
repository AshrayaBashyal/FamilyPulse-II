"""
Nurse's own analytics — nurses only see their own data.
"""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from apps.hospitals.models import HospitalMembership
from apps.analytics.services import nurse_analytics
from .utils import parse_date_params, parse_group_by


class NurseVisitSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Nurse's own visit summary", tags=["Analytics"])
    def get(self, request):
        date_from, date_to = parse_date_params(request)
        hospital_id = request.query_params.get("hospital")

        hospital = None
        if hospital_id:
            # Verify the nurse actually belongs to this hospital
            membership = HospitalMembership.objects.filter(
                user=request.user,
                hospital_id=hospital_id,
                role=HospitalMembership.Role.NURSE,
                is_active=True,
            ).select_related("hospital").first()
            if membership:
                hospital = membership.hospital

        data = nurse_analytics.nurse_visit_summary(
            request.user, hospital=hospital,
            date_from=date_from, date_to=date_to,
        )
        return Response(data)


class NurseVisitsOverTimeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Nurse's visits over time", tags=["Analytics"])
    def get(self, request):
        date_from, date_to = parse_date_params(request)
        group_by = parse_group_by(request, default="week")
        data = nurse_analytics.nurse_visits_over_time(
            request.user, date_from=date_from, date_to=date_to, group_by=group_by,
        )
        return Response(data)


class NurseReportSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Nurse's own report summary", tags=["Analytics"])
    def get(self, request):
        date_from, date_to = parse_date_params(request)
        data = nurse_analytics.nurse_report_summary(
            request.user, date_from=date_from, date_to=date_to,
        )
        return Response(data)