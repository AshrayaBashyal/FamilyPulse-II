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