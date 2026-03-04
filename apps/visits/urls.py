from django.urls import path
from apps.visits.views.visit import VisitListCreateView, VisitDetailView, VisitTypeListCreateView
from apps.visits.views.lifecycle import (
    ScheduleVisitView,
    AssignNurseView,
    AcceptVisitView,
    StartVisitView,
    CompleteVisitView,
    CancelVisitView,
)

urlpatterns = [
    # Visit types
    path("types/", VisitTypeListCreateView.as_view(), name="visit-type-list-create"),

    # Visits
    path("", VisitListCreateView.as_view(), name="visit-list-create"),
    path("<uuid:visit_id>/", VisitDetailView.as_view(), name="visit-detail"),

    # Lifecycle transitions 
    path("<uuid:visit_id>/schedule/", ScheduleVisitView.as_view(), name="visit-schedule"),
    path("<uuid:visit_id>/assign/", AssignNurseView.as_view(), name="visit-assign"),
    path("<uuid:visit_id>/accept/", AcceptVisitView.as_view(), name="visit-accept"),
    path("<uuid:visit_id>/start/", StartVisitView.as_view(), name="visit-start"),
    path("<uuid:visit_id>/complete/", CompleteVisitView.as_view(), name="visit-complete"),
    path("<uuid:visit_id>/cancel/", CancelVisitView.as_view(), name="visit-cancel"),
]