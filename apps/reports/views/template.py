from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from apps.reports.models import ReportTemplate, TemplateField
from apps.reports.serializers.report import ReportTemplateSerializer, CreateReportTemplateSerializer, TemplateFieldSerializer
from apps.hospitals.models import HospitalMembership
from apps.visits.models import VisitType


def is_hospital_admin_of_visit_type(user, visit_type) -> bool:
    return HospitalMembership.objects.filter(
        user=user,
        hospital=visit_type.hospital,
        role=HospitalMembership.Role.HOSPITAL_ADMIN,
        is_active=True,
    ).exists()