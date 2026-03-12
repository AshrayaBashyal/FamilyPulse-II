from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse
 
from apps.reports.models import Report
from apps.reports.serializers.report import (
    ReportSerializer,
    CreateReportSerializer,
    UpdateReportSerializer,
)
from apps.reports.services import report_service
from apps.hospitals.models import HospitalMembership
from apps.dependents.models import Guardianship
 

def get_report_or_404(report_id):
    try:
        return Report.objects.select_related(
            "visit__hospital", "visit__dependent",
            "visit__visit_type__report_template",
            "nurse", "reviewed_by",
        ).prefetch_related(
            "sections__field",
            "versions",
        ).get(id=report_id)
    except Report.DoesNotExist:
        return None 
    

def can_access_report(user, report) -> bool:
    # Assigned nurse
    if report.nurse_id == user.id:
        return True

    is_admin = HospitalMembership.objects.filter(
        user=user,
        hospital=report.visit.hospital,
        role__in=["hospital_admin", "medical_admin"],
        is_active=True,
    ).exists()
    if is_admin:
        return True

    is_guardian = Guardianship.objects.filter(
        user=user,
        dependent=report.visit.dependent,
        is_active=True,
    ).exists()
    if is_guardian:
        return True

    return False