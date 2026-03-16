from rest_framework import serializers
from apps.visits.models import Visit, VisitType, VisitAssignment


class VisitTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitType
        fields = [
            "id", "hospital", "name", "description",
            "duration_minutes", "price", "is_active",
        ]
        read_only_fields = ["id"]


class AssignedNurseSerializer(serializers.Serializer):
    """Lightweight nurse info embedded in VisitSerializer."""
    assignment_id    = serializers.UUIDField(source="id")
    nurse_id         = serializers.UUIDField(source="nurse.id")
    nurse_name       = serializers.CharField(source="nurse.full_name")
    nurse_email      = serializers.EmailField(source="nurse.email")
    assignment_status = serializers.CharField(source="status")


class VisitSerializer(serializers.ModelSerializer):
    dependent_name     = serializers.CharField(source="dependent.full_name", read_only=True)
    visit_type_name    = serializers.CharField(source="visit_type.name", read_only=True)
    hospital_name      = serializers.CharField(source="hospital.name", read_only=True)
    requested_by_email = serializers.EmailField(source="requested_by.email", read_only=True)
    assigned_nurse     = serializers.SerializerMethodField()

    # NEW: human-readable guardian response status
    awaiting_guardian_response  = serializers.BooleanField(read_only=True)
    is_confirmed_by_guardian    = serializers.BooleanField(read_only=True)

    class Meta:
        model = Visit
        fields = [
            "id",
            "hospital",
            "hospital_name",
            "dependent",
            "dependent_name",
            "visit_type",
            "visit_type_name",
            "requested_by",
            "requested_by_email",
            "assigned_nurse",
            "address",
            "latitude",
            "longitude",
            # NEW fields
            "preferred_at",
            "scheduled_at",
            "guardian_response",
            "guardian_response_at",
            "guardian_response_deadline",
            "awaiting_guardian_response",
            "is_confirmed_by_guardian",
            # ---
            "status",
            "guardian_notes",
            "cancellation_reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id", "requested_by", "status",
            "scheduled_at",
            "guardian_response", "guardian_response_at", "guardian_response_deadline",
            "awaiting_guardian_response", "is_confirmed_by_guardian",
            "created_at", "updated_at",
        ]

    def get_assigned_nurse(self, visit):
        assignment = visit.assignments.filter(
            status__in=[
                VisitAssignment.AssignmentStatus.PENDING,
                VisitAssignment.AssignmentStatus.ACCEPTED,
            ]
        ).select_related("nurse").first()
        if not assignment:
            return None
        return AssignedNurseSerializer(assignment).data


class CreateVisitSerializer(serializers.ModelSerializer):
    """
    CHANGE: preferred_at added — required, must be at least 48h from now.
    Validated here so the error is returned before hitting the service.
    """
    class Meta:
        model = Visit
        fields = [
            "hospital",
            "dependent",
            "visit_type",
            "address",
            "latitude",
            "longitude",
            "preferred_at",
            "guardian_notes",
        ]

    def validate_preferred_at(self, value):
        from django.conf import settings
        from django.utils import timezone
        from datetime import timedelta

        min_hours = getattr(settings, "VISIT_MIN_ADVANCE_HOURS", 48)
        min_allowed = timezone.now() + timedelta(hours=min_hours)

        if value < min_allowed:
            raise serializers.ValidationError(
                f"preferred_at must be at least {min_hours} hours from now."
            )
        return value


class VisitAssignmentSerializer(serializers.ModelSerializer):
    nurse_email = serializers.EmailField(source="nurse.email", read_only=True)
    nurse_name  = serializers.CharField(source="nurse.full_name", read_only=True)

    class Meta:
        model = VisitAssignment
        fields = [
            "id", "visit", "nurse", "nurse_email", "nurse_name",
            "assigned_by", "status", "rejection_reason",
            "accepted_at", "rejected_at", "created_at",
        ]
        read_only_fields = fields