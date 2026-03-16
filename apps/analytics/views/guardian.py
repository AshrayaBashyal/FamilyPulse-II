"""
Guardian analytics — health trends for their dependents.
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from apps.dependents.models import Dependent, Guardianship
from apps.analytics.services import guardian_analytics
from .utils import parse_date_params


def get_dependent_for_guardian(user, dependent_id):
    """
    Returns the dependent if the user is an active guardian, else None.
    """
    try:
        dependent = Dependent.objects.get(id=dependent_id)
    except Dependent.DoesNotExist:
        return None

    is_guardian = Guardianship.objects.filter(
        user=user, dependent=dependent, is_active=True,
    ).exists()

    return dependent if is_guardian else None


class DependentVisitSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Dependent visit summary (guardian)", tags=["Analytics"])
    def get(self, request, dependent_id):
        dependent = get_dependent_for_guardian(request.user, dependent_id)
        if not dependent:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        date_from, date_to = parse_date_params(request)
        data = guardian_analytics.dependent_visit_summary(dependent, date_from, date_to)
        return Response(data)


class DependentHealthTrendsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Dependent health trends (guardian)", tags=["Analytics"])
    def get(self, request, dependent_id):
        dependent = get_dependent_for_guardian(request.user, dependent_id)
        if not dependent:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        field_name = request.query_params.get("field")
        if not field_name:
            return Response(
                {"detail": "field query param is required. Use /health/fields/ to see available fields."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        date_from, date_to = parse_date_params(request)
        data = guardian_analytics.dependent_health_trends(
            dependent, field_name=field_name,
            date_from=date_from, date_to=date_to,
        )
        return Response(data)


class DependentAvailableFieldsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List available health trend fields for a dependent (guardian)",
        tags=["Analytics"],
    )
    def get(self, request, dependent_id):
        dependent = get_dependent_for_guardian(request.user, dependent_id)
        if not dependent:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        fields = guardian_analytics.dependent_available_trend_fields(dependent)
        return Response({"fields": fields})