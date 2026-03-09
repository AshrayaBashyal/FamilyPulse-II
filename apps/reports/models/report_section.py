"""
One filled-in field per report. Value always stored as text,
interpreted by field.field_type.
"""

from django.db import models
from common.models import UUIDModel
from apps.reports.models.report import Report
from apps.reports.models.report_template import TemplateField


class ReportSection(UUIDModel):

    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="sections")
    field = models.ForeignKey(
        TemplateField,
        on_delete=models.PROTECT,
        related_name="sections",
    )
    value = models.TextField(blank=True, default="")

    class Meta:
        db_table = "reports_section"
        unique_together = [("report", "field")]
        indexes = [
            models.Index(fields=["field"]),
            # Analytics will query sections by field to aggregate values
            # e.g. "all temperature readings for this patient"
        ]

    def __str__(self):
        return f"{self.field.label}: {self.value[:50]}"