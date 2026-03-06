import uuid
from django.db import models
from common.models import UUIDModel


class Hospital(UUIDModel):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"

    name = models.CharField(max_length=255)

    registration_number = models.CharField(max_length=100, unique=True,)

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, default="")

    address = models.TextField(blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    country = models.CharField(max_length=100, blank=True, default="")

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING,)

    # Optional logo URL — actual file uploads later
    logo_url = models.URLField(blank=True, default="")

    class Meta:
        db_table = "hospitals_hospital"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.status})"

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE

    @property
    def is_suspended(self):
        return self.status == self.Status.SUSPENDED