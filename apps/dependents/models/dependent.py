from django.db import models
from common.mixins import UUIDModel


class Dependent(UUIDModel):

    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"
        PREFER_NOT_TO_SAY = "prefer_not_to_say", "Prefer not to say"

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    date_of_birth = models.DateField(null=True, blank=True)

    gender = models.CharField(max_length=20, choices=Gender.choices, blank=True, default="",)

    medical_history = models.TextField(blank=True, default="", help_text="Free text. Guardians describe relevant history.",)

    allergies = models.TextField(blank=True, default="", help_text="List known allergies.",)

    chronic_conditions = models.TextField(blank=True, default="", help_text="Ongoing conditions the care team should know about.",)

    emergency_notes = models.TextField(blank=True, default="", help_text="Critical info for emergencies — blood type, emergency contact, etc.")

    class Meta:
        db_table = "dependents_dependent"
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        raw_name = f"{self.first_name} {self.last_name}"
        return " ".join(raw_name.split())