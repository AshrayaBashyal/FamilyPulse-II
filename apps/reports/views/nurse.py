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


class ReportListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: ReportSerializer(many=True)},
        summary="List reports for a visit",
        tags=["Reports"],
    )
    def get(self, request):
        visit_id = request.query_params.get("visit")
        if not visit_id:
            return Response(
                {"detail": "visit query param is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reports = Report.objects.filter(visit_id=visit_id).select_related(
            "nurse", "reviewed_by", "visit__hospital", "visit__dependent"
        ).prefetch_related("sections__field", "versions")

        accessible = [r for r in reports if can_access_report(request.user, r)]
        return Response(ReportSerializer(accessible, many=True).data)
 

    #Better Version:
    # from django.db.models import Q

    # def get(self, request):
    #     visit_id = request.query_params.get("visit")
    #     user = request.user
        
    #     # 1. Define the filters for accessibility
    #     # (Matches your logic in can_access_report)
    #     accessible_filter = Q(nurse=user) | \
    #                         Q(visit__hospital__memberships__user=user, 
    #                         visit__hospital__memberships__is_active=True) | \
    #                         Q(visit__dependent__guardianships__user=user, 
    #                         visit__dependent__guardianships__is_active=True)

    #     # 2. Combine with the visit_id filter
    #     reports = Report.objects.filter(
    #         Q(visit_id=visit_id) & accessible_filter
    #     ).distinct().select_related(
    #         "nurse", "reviewed_by", "visit__hospital", "visit__dependent"
    #     ).prefetch_related("sections__field", "versions")

    #     return Response(ReportSerializer(reports, many=True).data)

    @extend_schema(
        request=CreateReportSerializer,
        responses={201: ReportSerializer},
        summary="Create a report (nurse)",
        tags=["Reports"],
    )
    def post(self, request):
        serializer = CreateReportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
        report = report_service.create_report(
            visit_id=serializer.validated_data["visit"],
            sections_input=serializer.validated_data["sections"],
            nurse=request.user,
        )
        return Response(ReportSerializer(report).data, status=status.HTTP_201_CREATED)
 

class ReportDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: ReportSerializer},
        summary="Get report detail",
        tags=["Reports"]
    )
    def get(self, request, report_id):
        report = get_report_or_404(report_id)
        if not report or not can_access_report(request.user, report):
            return Response({"detail": "Report not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ReportSerializer(report).data)
    

    @extend_schema(
        request=UpdateReportSerializer,
        responses={200: ReportSerializer}, 
        summary="Update a draft report (nurse)", 
        tags=["Reports"]
    )
    def patch(self, request, report_id):
        report = get_report_or_404(report_id)
        if not report or not can_access_report(request.user, report):
            return Response({"detail": "Report not found."}, status=status.HTTP_404_NOT_FOUND)

        # if report.nurse != request.user:     NOT NEEDED  can_access_report CAN HANDLE THIS
        #     return Response({"detail": "Only the nurse who created this report can edit it."}, status=status.HTTP_403_FORBIDDEN)

        serializer = UpdateReportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        report = report_service.update_report(report, serializer.validated_data["sections"])    
        return Response(ReportSerializer(report).data)


    @extend_schema(
        responses={204: OpenApiResponse(description="Deleted")},
        summary="Delete a draft report (nurse)",
        tags=["Reports"]
    )
    def delete(self, request, report_id):
        report = get_report_or_404(report_id)
        if not report or not can_access_report(request.user, report):
            return Response({"detail": "Report not found."}, status=status.HTTP_404_NOT_FOUND)

        report_service.delete_report(report)            
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReportSubmitView(APIView):
    permission_classes = [IsAuthenticated]
 
    @extend_schema(
        responses={200: ReportSerializer}, 
        summary="Submit report for review (nurse)", 
        tags=["Reports"]
    )
    def post(self, request, report_id):
        report = get_report_or_404(report_id)
        if not report:
            return Response({"detail": "Report not found."}, status=status.HTTP_404_NOT_FOUND)
        if report.nurse != request.user:
            return Response({"detail": "Only the nurse who created this report can submit it."}, status=status.HTTP_403_FORBIDDEN)
 
        report = report_service.submit_report(report, nurse=request.user)
        return Response(ReportSerializer(report).data)