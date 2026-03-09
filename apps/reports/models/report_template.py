from django.db import models
from common.models import UUIDModel
from apps.visits.models.visit_type import VisitType


class ReportTemplate(UUIDModel):
    visit_type = models.OneToOneField(
        VisitType,
        on_delete=models.CASCADE,
        related_name="report_template",
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Instructions for the nurse filling this report.",
    )

    class Meta:
        db_table = "reports_template"

    def __str__(self):
        return f"Template for {self.visit_type.name}"


class TemplateField(UUIDModel):

    class FieldType(models.TextChoices):
        TEXT           = "text",           "Text"
        NUMBER         = "number",         "Number"
        BLOOD_PRESSURE = "blood_pressure", "Blood Pressure"
        CHOICE         = "choice",         "Choice"
        BOOLEAN        = "boolean",        "Boolean"
        ATTACHMENT     = "attachment",     "Attachment"

    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, related_name="fields")

    name = models.CharField(max_length=100, help_text="Machine-readable key e.g. 'wound_condition'.")
    label = models.CharField(max_length=200, help_text="Human-readable label e.g. 'Wound Condition'.")
    field_type = models.CharField(max_length=20, choices=FieldType.choices, default=FieldType.TEXT)
    required = models.BooleanField(default=True)   # Determines whether the nurse must fill the field.

    choices = models.JSONField(
        default=list,
        blank=True,
        help_text="Options for choice fields. e.g. ['healing', 'infected', 'stable']",
    )

    order = models.PositiveIntegerField(default=0)
    help_text = models.CharField(max_length=300, blank=True, default="")

    class Meta:
        db_table = "reports_template_field"
        ordering = ["order"]
        unique_together = [("template", "name")]

    def __str__(self):
        return f"{self.label} ({self.field_type}) — {self.template.visit_type.name}"