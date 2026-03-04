from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class ScheduleVisitSerializer(serializers.Serializer):
    scheduled_at = serializers.DateTimeField()


class AssignNurseSerializer(serializers.Serializer):
    nurse_id = serializers.UUIDField()

    def validate_nurse_id(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("No user found with this ID.")
        return value


class CancelVisitSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, default="", allow_blank=True)


class RejectVisitSerializer(serializers.Serializer):
    """Used by medical admin when rejecting a submitted report."""
    reason = serializers.CharField(min_length=10)
    # Rejection requires a reason — min_length enforces a meaningful message.


class RejectAssignmentSerializer(serializers.Serializer):
    """Used by nurse when rejecting a visit assignment."""
    reason = serializers.CharField(
        required=False,
        default="",
        allow_blank=True,
        help_text="Optional reason for rejecting the assignment.",
    )    