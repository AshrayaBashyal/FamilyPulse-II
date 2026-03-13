from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
 
from apps.reports.models import Report
from apps.reports.serializers.report import ReportSerializer, ReviewReportSerializer
from apps.reports.services import report_service
from apps.hospitals.models import HospitalMembership


class ReportReviewView(APIView):
    """
    Medical admin either approves or rejects with a single endpoint.
    Action is determined by the "action" field in the request body.
    """
    permission_classes = [IsAuthenticated]

    def get_report(self, report_id):
        try:
            return Report.objects.select_related(
                "visit__hospital", "nurse", "reviewed_by"
            ).prefetch_related("versions").get(id=report_id)
        except Report.DoesNotExist:
            return None

    extend_schema(
        request=ReviewReportSerializer,
        responses={200: ReportSerializer},
        summary="Approve or reject a report (medical admin)",
        tags=["Reports"],
    )
    def post(self, request, report_id):
        report = self.get_report(report_id)
        if not report:
            return Response({"detail": "Report not found."}, status=status.HTTP_404_NOT_FOUND)

        # Must be medical admin of this hospital
        is_medical_admin = HospitalMembership.objects.filter(
            user=request.user,
            hospital=report.visit.hospital,
            role=HospitalMembership.Role.MEDICAL_ADMIN,
            is_active=True,
        ).exists()
        if not is_medical_admin:
            return Response(
                {"detail": "Only a medical admin of this hospital can review reports."},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        serializer = ReviewReportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        action = serializer.validated_data["action"]
        review_notes = serializer.validated_data["review_notes", ""]

        if action == "accept":
            report = report_service.approve_report(
                report=report,
                medical_admin=request.user,
                review_notes=review_notes,
            )
        else:
            report = report_service.reject_report(
                report=report,
                medical_admin=request.user,
                review_notes=review_notes,
            )    

        return Response(ReportSerializer(report).data)   