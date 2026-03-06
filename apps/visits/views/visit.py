from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.visits.models import Visit, VisitType
from apps.visits.serializers.visit import VisitSerializer, CreateVisitSerializer, VisitTypeSerializer
from apps.visits.services import visit_service
from apps.hospitals.models import HospitalMembership
from apps.dependents.models import Guardianship


class VisitListCreateView(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: VisitSerializer(many=True)},
        summary="List visits (scoped to user's role)",
        tags=["Visits"],
    )
    def get(self, request):
        user = request.user

        # - Guardian: sees visits for their dependents
        # - Nurse: sees visits assigned to them
        # - Admin/Medical Admin: sees all visits in their hospitals

        memberships = HospitalMembership.objects.filter(
            user=user, is_active=True
        ).values_list("hospital_id", "role")

        hospital_ids_as_admin = [
            hid for hid, role in memberships
            if role in [HospitalMembership.Role.HOSPITAL_ADMIN, HospitalMembership.Role.MEDICAL_ADMIN]
        ]
        hospital_ids_as_nurse = [
            hid for hid, role in memberships
            if role == HospitalMembership.Role.NURSE
        ]

        dependent_ids = Guardianship.objects.filter(
            user=user, is_active=True
        ).values_list("dependent_id", flat=True)

        from django.db.models import Q
        visits = Visit.objects.filter(
            Q(dependent_id__in=dependent_ids) |               # as guardian
            Q(assignments__nurse=user) |                      # as nurse (any assignment status — pending or accepted)|                # as nurse
            Q(hospital_id__in=hospital_ids_as_admin)          # as admin
        ).select_related(
            "dependent", "visit_type", "hospital", "requested_by"
        ).distinct()

        return Response(VisitSerializer(visits, many=True).data)

    @extend_schema(
        request=CreateVisitSerializer,
        responses={201: VisitSerializer},
        summary="Book a visit",
        tags=["Visits"],
    )
    def post(self, request):
        serializer = CreateVisitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        visit = visit_service.create_visit(
            validated_data=serializer.validated_data,
            requested_by=request.user,
        )
        return Response(VisitSerializer(visit).data, status=status.HTTP_201_CREATED)


class VisitDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, visit_id, user):
        try:
            visit = Visit.objects.select_related(
                "dependent", "visit_type", "hospital", "requested_by"
            ).get(id=visit_id)
        except Visit.DoesNotExist:
            return None

        memberships = HospitalMembership.objects.filter(
            user=user, hospital=visit.hospital, is_active=True
        ).exists()

        is_guardian = Guardianship.objects.filter(
            user=user, dependent=visit.dependent, is_active=True
        ).exists()

        is_assigned_nurse = visit.assignments.filter(
            nurse=user, status="accepted"
        ).exists()

        if memberships or is_guardian or is_assigned_nurse:
            return visit
        return None

    @extend_schema(
        responses={200: VisitSerializer},
        summary="Get visit detail",
        tags=["Visits"],
    )
    def get(self, request, visit_id):
        visit = self.get_object(visit_id, request.user)
        if not visit:
            return Response({"detail": "Visit not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(VisitSerializer(visit).data)


class VisitTypeListCreateView(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: VisitTypeSerializer(many=True)},
        summary="List visit types",
        tags=["Visit Types"],
    )
    def get(self, request):
        hospital_id = request.query_params.get("hospital")
        if not hospital_id:
            return Response(
                {"detail": "hospital query param is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        types = VisitType.objects.filter(hospital_id=hospital_id, is_active=True)
        return Response(VisitTypeSerializer(types, many=True).data)

    @extend_schema(
        request=VisitTypeSerializer,
        responses={201: VisitTypeSerializer},
        summary="Create a visit type (hospital admin)",
        tags=["Visit Types"],
    )
    def post(self, request):
        serializer = VisitTypeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Verify user is admin of this hospital
        hospital = serializer.validated_data["hospital"]
        is_admin = HospitalMembership.objects.filter(
            user=request.user,
            hospital=hospital,
            role=HospitalMembership.Role.HOSPITAL_ADMIN,
            is_active=True,
        ).exists()
        if not is_admin:
            return Response(
                {"detail": "Only hospital admins can create visit types."},
                status=status.HTTP_403_FORBIDDEN,
            )

        visit_type = serializer.save()
        return Response(VisitTypeSerializer(visit_type).data, status=status.HTTP_201_CREATED)
    

    
class VisitAssignmentHistoryView(APIView):
    """
    Returns the full assignment history for a visit.
    Shows every nurse who was ever assigned, their status, and timestamps.

    Useful for:
    - Guardian: seeing who is/was assigned to their dependent's visit
    - Admin: auditing assignment history
    - Medical admin: context when reviewing reports
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: "VisitAssignmentSerializer(many=True)"},
        summary="List assignment history for a visit",
        tags=["Visits"],
    )
    def get(self, request, visit_id):
        from apps.visits.serializers.visit import VisitAssignmentSerializer
        from apps.visits.models import VisitAssignment

        try:
            visit = Visit.objects.select_related("hospital", "dependent").get(id=visit_id)
        except Visit.DoesNotExist:
            return Response({"detail": "Visit not found."}, status=status.HTTP_404_NOT_FOUND)

        # Same access check as VisitDetailView
        is_member = HospitalMembership.objects.filter(
            user=request.user, hospital=visit.hospital, is_active=True
        ).exists()
        is_guardian = Guardianship.objects.filter(
            user=request.user, dependent=visit.dependent, is_active=True
        ).exists()

        if not is_member and not is_guardian:
            return Response({"detail": "Visit not found."}, status=status.HTTP_404_NOT_FOUND)

        assignments = VisitAssignment.objects.filter(
            visit=visit
        ).select_related("nurse", "assigned_by").order_by("-created_at")

        return Response(VisitAssignmentSerializer(assignments, many=True).data)