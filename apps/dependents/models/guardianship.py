from django.db import models
from django.conf import settings
from common.models import UUIDModel
from apps.dependents.models.dependent import Dependent


class Guardianship(UUIDModel):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="guardianships",
        # user.guardianships.all() → all dependents this user manages
    )

    dependent = models.ForeignKey(Dependent, on_delete=models.CASCADE, related_name="guardianships",
        # dependent.guardianships.all() → all guardians for this dependent
    )

    is_active = models.BooleanField(default=True)

    # delegating access (future feature).
    # Could be the user themselves (self-added) or another guardian
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="granted_guardianships",)

    class Meta:
        db_table = "dependents_guardianship"
        unique_together = [("user", "dependent")]

    def __str__(self):
        return f"{self.user.email} → {self.dependent.full_name}"