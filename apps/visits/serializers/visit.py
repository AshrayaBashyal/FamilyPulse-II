from rest_framework import serializers
from apps.visits.models import Visit, VisitType, VisitAssignment


class VisitTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitType
        fields = [
            "id", "hospital", "name", "description",
            "duration_minutes", "price",
            "is_active",
        ]
        read_only_fields = ["id"]


class AssignedNurseSerializer(serializers.Serializer):
    """Lightweight nurse info embedded in VisitSerializer."""
    assignment_id = serializers.UUIDField(source="id")
    nurse_id = serializers.UUIDField(source="nurse.id")
    nurse_name = serializers.CharField(source="nurse.full_name")
    nurse_email = serializers.EmailField(source="nurse.email")
    assignment_status = serializers.CharField(source="status")


class VisitSerializer(serializers.ModelSerializer):
    """Full visit detail."""

    dependent_name = serializers.CharField(source="dependent.full_name", read_only=True)
    visit_type_name = serializers.CharField(source="visit_type.name", read_only=True)
    hospital_name = serializers.CharField(source="hospital.name", read_only=True)
    requested_by_email = serializers.EmailField(source="requested_by.email", read_only=True)
    assigned_nurse = serializers.SerializerMethodField()

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
            "scheduled_at",
            "status",
            "guardian_notes",
            "cancellation_reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id", "requested_by", "status",
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
    """Used when a guardian books a visit."""

    class Meta:
        model = Visit
        fields = [
            "hospital",
            "dependent",
            "visit_type",
            "address",
            "latitude",
            "longitude",
            "scheduled_at",
            "guardian_notes",
        ]


class VisitAssignmentSerializer(serializers.ModelSerializer):
    nurse_email = serializers.EmailField(source="nurse.email", read_only=True)
    nurse_name = serializers.CharField(source="nurse.full_name", read_only=True)

    class Meta:
        model = VisitAssignment
        fields = [
            "id", "visit", "nurse", "nurse_email", "nurse_name",
            "assigned_by", "status", "rejection_reason",
            "accepted_at", "rejected_at", "created_at",
        ]
        read_only_fields = fields