"""
All aggregation queries live here. Views stay thin.
No new models — everything is computed from visits, reports, assignments.

TODO (post-production):
- Add caching (django.core.cache) on all functions, keyed by args, TTL 10min.
- Add pagination to hospital_nurse_summary and hospital_visits_over_time.

TODO (payments integration):
- Add superadmin_financial_summary() covering:
    total revenue across all hospitals, revenue per hospital, revenue per visit type,
    outstanding payments, refunds, monthly revenue trend.
- Add hospital_financial_summary() for hospital admin:
    revenue this month, per visit type breakdown, unpaid invoices.
- Hook into Payment model once apps/payments is built.
"""

from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from apps.visits.models import Visit
 
 
def date_filter(qs, field: str, date_from=None, date_to=None):
    """Apply optional date range filter to a queryset."""
    if date_from:
        qs = qs.filter(**{f"{field}__date__gte": date_from})
    if date_to:
        qs = qs.filter(**{f"{field}__date__lte": date_to})
    return qs
 
 
TRUNC_MAP = {
    "day": TruncDate,
    "week": TruncWeek,
    "month": TruncMonth,
}
 
# Statuses that mean the nurse successfully delivered the visit
COMPLETED_STATUSES = [
    Visit.Status.COMPLETED,
    Visit.Status.REPORT_SUBMITTED,
    Visit.Status.APPROVED,
]