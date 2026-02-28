from django.urls import path
from apps.hospitals.views.hospital import (
    HospitalListCreateView,
    HospitalDetailView,
    HospitalStatusView,
    MyHospitalsView
)
from apps.hospitals.views.staff import StaffListAddView, StaffDetailView

urlpatterns = [
    # Hospital 
    path("mine/", MyHospitalsView.as_view(), name="hospital-mine"),

    path("", HospitalListCreateView.as_view(), name="hospital-list-create"),
    path("<uuid:hospital_id>/", HospitalDetailView.as_view(), name="hospital-detail"),
    path("<uuid:hospital_id>/status/", HospitalStatusView.as_view(), name="hospital-status"),

    # Staff management 
    path("<uuid:hospital_id>/staff/", StaffListAddView.as_view(), name="staff-list-add"),
    path("<uuid:hospital_id>/staff/<uuid:membership_id>/", StaffDetailView.as_view(), name="staff-detail"),
]