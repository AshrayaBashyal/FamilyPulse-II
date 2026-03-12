from rest_framework import serializers
from apps.reports.models import Report, ReportVersion, ReportTemplate, TemplateField, ReportSection


class TemplateFieldSerializer(serializers.ModelSerializer):
    choices = serializers.ListField(
        child = serializers.CharField,
        required = False,
        default = list,
    )

    class Meta:
        model = TemplateField
        fields = [
            "id", "name", "label", "field_type",
            "required", "choices", "order", "help_text",
        ]
        read_only_fields = ["id"]


class CreateReportTemplateSerializer(serializers.Serializer):     # class CreateReportTemplateSerializer(serializers.ModelSerializer)??
    """
    Used when hospital admin creates a template.
    """
    # visit_type = serializers.PrimaryKeyRelatedField(
    #     queryset=__import__(
    #         "apps.visits.models", fromlist=["VisitType"]
    #     ).VisitType.objects.all()
    # )
    from apps.visits.models import VisitType

    visit_type = serializers.PrimaryKeyRelatedField(
    queryset=VisitType.objects.all()
    )
    description = serializers.CharField(required=False, allow_blank=True, default="")
 

class ReportTemplateSerializer(serializers.ModelSerializer):
    """Read-only full template with all fields. Used for GET."""
    fields = TemplateFieldSerializer(many=True, read_only=True)
 
    class Meta:
        model = ReportTemplate
        fields = ["id", "visit_type", "description", "fields"]
        read_only_fields = ["id"]


class ReportSectionSerializer(serializers.ModelSerializer):
    field_name = serializers.CharField(source="field.name", read_only=True)
    field_label = serializers.CharField(source="field.label", read_only=True)
    field_type = serializers.CharField(source="field.field_type", read_only=True)
 
    class Meta:
        model = ReportSection
        fields = ["id", "field", "field_name", "field_label", "field_type", "value"]
        read_only_fields = ["id", "field_name", "field_label", "field_type"]
 
 
class ReportSectionInputSerializer(serializers.Serializer):
    field_id = serializers.UUIDField()
    value = serializers.CharField(allow_blank=True)
 
 
class ReportVersionSerializer(serializers.ModelSerializer):
    triggered_by_email = serializers.EmailField(source="triggered_by.email", read_only=True)
 
    class Meta:
        model = ReportVersion
        fields = [
            "id", "version_number", "sections_snapshot",
            "action", "triggered_by", "triggered_by_email",
            "notes", "created_at",
        ]
        read_only_fields = fields
 
 
class ReportSerializer(serializers.ModelSerializer):
    nurse_email = serializers.EmailField(source="nurse.email", read_only=True)
    nurse_name = serializers.CharField(source="nurse.full_name", read_only=True)
    reviewed_by_email = serializers.EmailField(
        source="reviewed_by.email", read_only=True, default=None,
    )
    sections = ReportSectionSerializer(many=True, read_only=True)
    versions = ReportVersionSerializer(many=True, read_only=True)
    is_locked = serializers.BooleanField(read_only=True)
 
    class Meta:
        model = Report
        fields = [
            "id", "visit",
            "nurse", "nurse_email", "nurse_name",
            "status", "is_locked",
            "submitted_at",
            "sections",
            "reviewed_by", "reviewed_by_email",
            "reviewed_at", "review_notes",
            "version", "versions",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "nurse", "status", "is_locked", "submitted_at",
            "reviewed_by", "reviewed_at", "review_notes",
            "version", "versions", "created_at", "updated_at",
        ]
 
 
class CreateReportSerializer(serializers.Serializer):
    visit = serializers.UUIDField()
    sections = ReportSectionInputSerializer(many=True)
 
 
class UpdateReportSerializer(serializers.Serializer):
    sections = ReportSectionInputSerializer(many=True)
 
 
class ReviewReportSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["approve", "reject"])
    review_notes = serializers.CharField(required=False, allow_blank=True, default="")
 
    def validate(self, attrs):
        if attrs["action"] == "reject" and not attrs.get("review_notes"):
            raise serializers.ValidationError(
                {"review_notes": "Review notes are required when rejecting a report."}
            )
        return attrs        