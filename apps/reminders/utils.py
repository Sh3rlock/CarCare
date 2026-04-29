"""
Smart alert computation — derives alerts from existing insurance and part data.
Imported by both the reminder list view and the dashboard (Step 10).
"""
import datetime


def get_smart_alerts(vehicle):
    """
    Returns a list of alert dicts for the given vehicle, sorted by urgency
    (most overdue / soonest expiry first).

    Each dict has:
        category    str  "insurance" | "part"
        title       str  Human-readable label
        subtitle    str  Secondary descriptor
        days        int  Days until due (negative = overdue)
        url         str  Link to the related record
        is_overdue  bool
        is_soon     bool  True when 0 <= days <= 30
    """
    today = datetime.date.today()
    alerts = []

    # Insurance policies expiring within 60 days (including already expired)
    for policy in vehicle.insurance_policies.all():
        days = (policy.end_date - today).days
        if days <= 60:
            alerts.append(
                {
                    "category": "insurance",
                    "title": f"Insurance expiring — {policy.provider}",
                    "subtitle": policy.get_coverage_type_display(),
                    "days": days,
                    "url": policy.get_absolute_url(),
                    "is_overdue": days < 0,
                    "is_soon": 0 <= days <= 30,
                }
            )

    # Parts with a next_replacement_date that is overdue or within 30 days
    for part in vehicle.part_replacements.exclude(next_replacement_date=None):
        days = (part.next_replacement_date - today).days
        if days <= 30:
            alerts.append(
                {
                    "category": "part",
                    "title": f"{part.part_name} due",
                    "subtitle": part.get_part_type_display(),
                    "days": days,
                    "url": part.get_absolute_url(),
                    "is_overdue": days < 0,
                    "is_soon": 0 <= days <= 30,
                }
            )

    # Sort: most overdue first (lowest days), then soonest upcoming
    return sorted(alerts, key=lambda a: a["days"])
