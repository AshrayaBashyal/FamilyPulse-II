from rest_framework import serializers
from apps.reports.models import Report, ReportVersion, ReportTemplate, TemplateField, ReportSection


class TemplateFieldSeriailzer(serializers.ModelSerializer):
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
