from django.urls import path
from apps.dependents.views.dependent import (
    DependentListCreateView,
    DependentDetailView,
    GuardianListAddView,
    GuardianRevokeView,
)

urlpatterns = [
    # Dependent management
    path("", DependentListCreateView.as_view(), name="dependent-list-create"),
    path("<uuid:dependent_id>/", DependentDetailView.as_view(), name="dependent-detail"),

    # Guardian management 
    path("<uuid:dependent_id>/guardians/", GuardianListAddView.as_view(), name="guardian-list-add"),
    path("<uuid:dependent_id>/guardians/<uuid:guardianship_id>/", GuardianRevokeView.as_view(), name="guardian-revoke"),
]