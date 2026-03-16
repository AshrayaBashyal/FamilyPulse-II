"""
apps/analytics/views/superadmin.py

Platform-wide analytics for superadmin only.
All endpoints require request.user.is_staff (Django superadmin).
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from apps.analytics.services import superadmin_analytics
from .utils import parse_date_params, parse_group_by


class SuperadminPlatformSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        summary="Platform-wide summary (superadmin)",
        tags=["Analytics - Superadmin"],
    )
    def get(self, request):
        date_from, date_to = parse_date_params(request)
        data = superadmin_analytics.superadmin_platform_summary(date_from, date_to)
        return Response(data)


class SuperadminHospitalBreakdownView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        summary="Per-hospital activity breakdown (superadmin)",
        tags=["Analytics - Superadmin"],
    )
    def get(self, request):
        date_from, date_to = parse_date_params(request)
        data = superadmin_analytics.superadmin_hospital_breakdown(date_from, date_to)
        return Response(data)


class SuperadminVisitsOverTimeView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        summary="Platform-wide visits over time (superadmin)",
        tags=["Analytics - Superadmin"],
    )
    def get(self, request):
        date_from, date_to = parse_date_params(request)
        group_by = parse_group_by(request, default="day")
        data = superadmin_analytics.superadmin_visits_over_time(date_from, date_to, group_by)
        return Response(data)