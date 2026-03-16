from django.db import models
from django.conf import settings
from common.models import UUIDModel
from apps.hospitals.models import Hospital
from apps.dependents.models import Dependent
from apps.visits.models.visit_type import VisitType


class Visit(UUIDModel):

    class Status(models.TextChoices):
        REQUESTED         = "requested",         "Requested"
        SCHEDULED         = "scheduled",         "Scheduled"
        ASSIGNED          = "assigned",          "Assigned"
        ACCEPTED          = "accepted",          "Accepted"
        STARTED           = "started",           "Started"
        COMPLETED         = "completed",         "Completed"
        REPORT_SUBMITTED  = "report_submitted",  "Report Submitted"
        APPROVED          = "approved",          "Approved"
        REJECTED          = "rejected",          "Rejected"
        CANCELLED         = "cancelled",         "Cancelled"

    class GuardianResponse(models.TextChoices):
        PENDING        = "pending",        "Pending"
        CONFIRMED      = "confirmed",      "Confirmed"
        CANCELLED      = "cancelled",      "Cancelled"
        AUTO_CONFIRMED = "auto_confirmed", "Auto Confirmed"    


    hospital = models.ForeignKey(Hospital, on_delete=models.PROTECT, related_name="visits",)

    dependent = models.ForeignKey(Dependent, on_delete=models.PROTECT, related_name="visits",)

    visit_type = models.ForeignKey(VisitType, on_delete=models.PROTECT, related_name="visits",)

    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="requested_visits",)

    # Location (static — no live tracking)
    address = models.TextField()
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    # Guardian's requested time window — set at booking, never changed after
    preferred_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Guardian's preferred visit time. Set at booking, used by admin as reference.",
    )

    # Admin-confirmed visit time — set by schedule_visit()
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Admin-confirmed visit time.",
    )

    # State
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.REQUESTED,
        db_index=True,
        # db_index=True because we filter by status constantly
    )

    guardian_response = models.CharField(
        max_length=20,
        choices=GuardianResponse.choices,
        null=True,
        blank=True,
        help_text=(
            "Set to PENDING when admin schedules. "
            "Guardian confirms or cancels. "
            "Auto-confirmed if no response by deadline."
        ),
    )

    # When the guardian responded (confirmed or cancelled)
    guardian_response_at = models.DateTimeField(
        null=True,
        blank=True,
    )
 
    # Deadline for guardian to respond before auto-confirm kicks in
    # Set to scheduled_at creation time + VISIT_CONFIRMATION_HOURS from settings
    guardian_response_deadline = models.DateTimeField(
        null=True,
        blank=True,
        help_text="If guardian hasn't responded by this time, visit is auto-confirmed.",
    )

    # Cancellation
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cancelled_visits",
    )
    cancellation_reason = models.TextField(blank=True, default="")

    # Notes
    guardian_notes = models.TextField(
        blank=True,
        default="",
        help_text="Instructions or context from the guardian at booking time.",
    )

    class Meta:
        db_table = "visits_visit"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Visit({self.dependent.full_name}, {self.status}, {self.scheduled_at})"

    @property
    def is_confirmed_by_guardian(self) -> bool:
        """True if guardian explicitly confirmed or auto-confirmed."""
        return self.guardian_response in [
            self.GuardianResponse.CONFIRMED,
            self.GuardianResponse.AUTO_CONFIRMED,
        ]
 
    @property
    def awaiting_guardian_response(self) -> bool:
        return self.guardian_response == self.GuardianResponse.PENDING    