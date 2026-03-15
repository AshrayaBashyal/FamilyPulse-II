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


class ReportTemplateView(APIView):
    permission_classes=[IsAuthenticated]    
    
    @extend_schema(
        responses={200: ReportTemplateSerializer},
        summary="Get report template for a visit type",
        tags=["Report Templates"],
    )
    def get(self, request):
        visit_type_id = request.query_params.get("visit_type")
        if not visit_type_id:
            return Response({"detail":"visit_type query param required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            template = ReportTemplate.objects.prefetch_related("fields").get(visit_type_id=visit_type_id)
        except ReportTemplate.DoesNotExist:
            return Response({"detail": "No template found for this visit type."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ReportTemplateSerializer(template).data)


    @extend_schema(
        request=ReportTemplateSerializer,
        responses={200: ReportTemplateSerializer},
        summary="Create a report template for a visit type (hospital admin)",
        tags=["Report Templates"],
    )
    def post(self, request):
        serializer = CreateReportTemplateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
        visit_type = serializer.validated_data["visit_type"]
 
        if not is_hospital_admin_of_visit_type(request.user, visit_type):
            return Response({"detail": "Only hospital admins can create report templates."}, status=status.HTTP_403_FORBIDDEN)
 
        if ReportTemplate.objects.filter(visit_type=visit_type).exists():
            return Response({"detail": "A template already exists for this visit type."}, status=status.HTTP_400_BAD_REQUEST)
 
        template = ReportTemplate.objects.create(
            visit_type=visit_type,
            description=serializer.validated_data.get("description", ""),
        )
        return Response(ReportTemplateSerializer(template).data, status=status.HTTP_201_CREATED)        


class TemplateFieldListCreateView(APIView):
    permission_classes = [IsAuthenticated]
 
    @extend_schema(
        request=TemplateFieldSerializer,
        responses={201: TemplateFieldSerializer},
        summary="Add a field to a report template (hospital admin)",
        tags=["Report Templates"],
    )
    def post(self, request, template_id):
        try:
            template = ReportTemplate.objects.select_related("visit_type__hospital").get(id=template_id)
        except ReportTemplate.DoesNotExist:
            return Response({"detail": "Template not found."}, status=status.HTTP_404_NOT_FOUND)
 
        if not is_hospital_admin_of_visit_type(request.user, template.visit_type):
            return Response({"detail": "Only hospital admins can edit templates."}, status=status.HTTP_403_FORBIDDEN)
 
        serializer = TemplateFieldSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
        field = TemplateField.objects.create(template=template, **serializer.validated_data)
        return Response(TemplateFieldSerializer(field).data, status=status.HTTP_201_CREATED)        


 
class TemplateFieldDeleteView(APIView):
    permission_classes = [IsAuthenticated]
 
    @extend_schema(
        responses={204: None},
        summary="Remove a field from a template (hospital admin)",
        tags=["Report Templates"],
    )
    def delete(self, request, template_id, field_id):
        try:
            template = ReportTemplate.objects.select_related("visit_type__hospital").get(id=template_id)
            field = TemplateField.objects.get(id=field_id, template=template)
        except (ReportTemplate.DoesNotExist, TemplateField.DoesNotExist):
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
 
        if not is_hospital_admin_of_visit_type(request.user, template.visit_type):
            return Response({"detail": "Only hospital admins can edit templates."}, status=status.HTTP_403_FORBIDDEN)
 
        if field.sections.exists():
            return Response(
                {"detail": "This field has been used in existing reports and cannot be deleted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
 
        field.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)        