from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.visits.models import Visit
from apps.visits.serializers.visit import VisitSerializer
from apps.visits.serializers.scheduling import (
    ScheduleVisitSerializer,
    AssignNurseSerializer,
    CancelVisitSerializer,
    RejectAssignmentSerializer,
)
from apps.visits.services import visit_service

User = get_user_model()


def get_visit_or_404(visit_id):
    try:
        return Visit.objects.select_related("hospital", "dependent").get(id=visit_id)
    except Visit.DoesNotExist:
        return None


class ScheduleVisitView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ScheduleVisitSerializer,
        responses={200: VisitSerializer},
        summary="Schedule a visit (admin)",
        tags=["Visit Lifecycle"],
    )
    def post(self, request, visit_id):
        visit = get_visit_or_404(visit_id)
        if not visit:
            return Response({"detail": "Visit not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ScheduleVisitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        visit = visit_service.schedule_visit(
            visit=visit,
            scheduled_at=serializer.validated_data["scheduled_at"],
            triggered_by=request.user,
        )
        return Response(VisitSerializer(visit).data)


class AssignNurseView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=AssignNurseSerializer,
        responses={200: VisitSerializer},
        summary="Assign a nurse to a visit (admin)",
        tags=["Visit Lifecycle"],
    )
    def post(self, request, visit_id):
        visit = get_visit_or_404(visit_id)
        if not visit:
            return Response({"detail": "Visit not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AssignNurseSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        nurse = User.objects.get(id=serializer.validated_data["nurse_id"])
        visit_service.assign_nurse(visit=visit, nurse=nurse, assigned_by=request.user)
        return Response(VisitSerializer(visit).data)


class AcceptVisitView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: VisitSerializer},
        summary="Accept a visit assignment (nurse)",
        tags=["Visit Lifecycle"],
    )
    def post(self, request, visit_id):
        visit = get_visit_or_404(visit_id)
        if not visit:
            return Response({"detail": "Visit not found."}, status=status.HTTP_404_NOT_FOUND)

        visit = visit_service.accept_visit(visit=visit, nurse=request.user)
        return Response(VisitSerializer(visit).data)


class StartVisitView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: VisitSerializer},
        summary="Start a visit (nurse)",
        tags=["Visit Lifecycle"],
    )
    def post(self, request, visit_id):
        visit = get_visit_or_404(visit_id)
        if not visit:
            return Response({"detail": "Visit not found."}, status=status.HTTP_404_NOT_FOUND)

        visit = visit_service.start_visit(visit=visit, nurse=request.user)
        return Response(VisitSerializer(visit).data)


class CompleteVisitView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: VisitSerializer},
        summary="Complete a visit (nurse)",
        tags=["Visit Lifecycle"],
    )
    def post(self, request, visit_id):
        visit = get_visit_or_404(visit_id)
        if not visit:
            return Response({"detail": "Visit not found."}, status=status.HTTP_404_NOT_FOUND)

        visit = visit_service.complete_visit(visit=visit, nurse=request.user)
        return Response(VisitSerializer(visit).data)


class CancelVisitView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=CancelVisitSerializer,
        responses={200: VisitSerializer},
        summary="Cancel a visit (admin)",
        tags=["Visit Lifecycle"],
    )
    def post(self, request, visit_id):
        visit = get_visit_or_404(visit_id)
        if not visit:
            return Response({"detail": "Visit not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = CancelVisitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        visit = visit_service.cancel_visit(
            visit=visit,
            cancelled_by=request.user,
            reason=serializer.validated_data.get("reason", ""),
        )
        return Response(VisitSerializer(visit).data)


class RejectAssignmentView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=RejectAssignmentSerializer,
        responses={200: VisitSerializer},
        summary="Reject a visit assignment (nurse)",
        tags=["Visit Lifecycle"],
    )
    def post(self, request, visit_id):
        visit = get_visit_or_404(visit_id)
        if not visit:
            return Response({"detail": "Visit not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = RejectAssignmentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        visit = visit_service.reject_assignment(
            visit=visit,
            nurse=request.user,
            reason=serializer.validated_data.get("reason", ""),
        )
        return Response(VisitSerializer(visit).data)


# Guardian confirm scheduled time
class ConfirmVisitView(APIView):
    """
    Guardian confirms the admin-scheduled time.
    Works even if a nurse is already assigned (parallel flow).
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: VisitSerializer},
        summary="Confirm scheduled visit time (guardian)",
        tags=["Visit Lifecycle"],
    )
    def post(self, request, visit_id):
        visit = get_visit_or_404(visit_id)
        if not visit:
            return Response({"detail": "Visit not found."}, status=status.HTTP_404_NOT_FOUND)

        visit = visit_service.confirm_visit(visit=visit, guardian=request.user)
        return Response(VisitSerializer(visit).data)


# Guardian cancel due to unacceptable scheduled time
class GuardianCancelView(APIView):
    """
    Guardian rejects the scheduled time — visit is cancelled.
    Any existing nurse assignment is also cancelled.
    Guardian should rebook with a different time or hospital.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=CancelVisitSerializer,
        responses={200: VisitSerializer},
        summary="Cancel visit due to unacceptable scheduled time (guardian)",
        tags=["Visit Lifecycle"],
    )
    def post(self, request, visit_id):
        visit = get_visit_or_404(visit_id)
        if not visit:
            return Response({"detail": "Visit not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = CancelVisitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        visit = visit_service.cancel_by_guardian(
            visit=visit,
            guardian=request.user,
            reason=serializer.validated_data.get("reason", ""),
        )
        return Response(VisitSerializer(visit).data)


class SubmitReportView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: VisitSerializer},
        summary="Mark report as submitted (nurse)",
        tags=["Visit Lifecycle"],
    )
    def post(self, request, visit_id):
        visit = get_visit_or_404(visit_id)
        if not visit:
            return Response({"detail": "Visit not found."}, status=status.HTTP_404_NOT_FOUND)

        visit = visit_service.mark_report_submitted(visit=visit, nurse=request.user)
        return Response(VisitSerializer(visit).data)