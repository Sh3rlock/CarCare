import datetime
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView

from apps.garages.utils import get_active_garage
from apps.parts.models import PartReplacement
from apps.reminders.utils import get_smart_alerts
from apps.services.models import ServiceRecord, ServiceRecordItem
from apps.vehicles.models import Vehicle


def _enrich_vehicles(user, garage=None):
    today = datetime.date.today()
    enriched = []

    qs = Vehicle.objects.filter(garage=garage) if garage else Vehicle.objects.filter(owner=user)
    for vehicle in qs:
        smart_alerts = get_smart_alerts(vehicle)

        # Manual reminders that are overdue or due soon
        reminder_alerts = []
        for reminder in vehicle.reminders.filter(is_done=False):
            if reminder.is_overdue or reminder.is_due_soon:
                reminder_alerts.append(
                    {
                        "category": "reminder",
                        "title": reminder.title,
                        "subtitle": f"{vehicle.make} {vehicle.model}",
                        "days": reminder.days_until_due,
                        "url": reverse("reminders:list", kwargs={"vehicle_pk": vehicle.pk}),
                        "is_overdue": reminder.is_overdue,
                        "is_soon": reminder.is_due_soon,
                        "vehicle": vehicle,
                    }
                )

        all_vehicle_alerts = smart_alerts + reminder_alerts

        enriched.append(
            {
                "vehicle": vehicle,
                "alerts": all_vehicle_alerts,
                "overdue_count": sum(1 for a in all_vehicle_alerts if a["is_overdue"]),
                "soon_count": sum(1 for a in all_vehicle_alerts if a["is_soon"] and not a["is_overdue"]),
                "latest_mileage": vehicle.mileage_logs.order_by("-date", "-created_at").first(),
                "active_insurance": (
                    vehicle.insurance_policies
                    .filter(end_date__gte=today)
                    .order_by("end_date")
                    .first()
                ),
            }
        )

    return enriched


class LandingView(TemplateView):
    template_name = "landing.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        garage = get_active_garage(self.request)

        enriched_vehicles = _enrich_vehicles(user, garage)
        context["enriched_vehicles"] = enriched_vehicles
        context["vehicle_count"] = len(enriched_vehicles)

        all_alerts = []
        for ev in enriched_vehicles:
            for alert in ev["alerts"]:
                alert.setdefault("vehicle", ev["vehicle"])
                all_alerts.append(alert)
        all_alerts.sort(key=lambda a: (a["days"] is None, a["days"] if a["days"] is not None else 0))
        context["all_alerts"] = all_alerts

        vehicle_filter = {"vehicle__garage": garage} if garage else {"vehicle__owner": user}
        context["recent_services"] = (
            ServiceRecord.objects
            .filter(**vehicle_filter)
            .select_related("vehicle")
            .order_by("-date", "-created_at")[:5]
        )
        context["recent_parts"] = (
            PartReplacement.objects
            .filter(**vehicle_filter)
            .select_related("vehicle")
            .order_by("-date", "-created_at")[:5]
        )

        # KPI cards
        context["service_count"] = ServiceRecord.objects.filter(**vehicle_filter).count()
        context["part_count"] = PartReplacement.objects.filter(**vehicle_filter).count()
        context["overdue_alert_count"] = sum(1 for a in all_alerts if a["is_overdue"])
        context["soon_alert_count"] = sum(
            1 for a in all_alerts if a["is_soon"] and not a["is_overdue"]
        )
        context["total_service_cost"] = (
            ServiceRecord.objects.filter(**vehicle_filter).aggregate(total=Sum("cost"))["total"]
            or Decimal("0")
        )

        # Charts: last 6 months service trend
        six_months_ago = datetime.date.today() - datetime.timedelta(days=183)
        monthly = (
            ServiceRecord.objects
            .filter(**vehicle_filter, date__gte=six_months_ago)
            .annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(
                count=Count("id"),
                total_cost=Sum("cost"),
            )
            .order_by("month")
        )
        context["monthly_labels"] = [m["month"].strftime("%b %Y") for m in monthly]
        context["monthly_service_counts"] = [m["count"] for m in monthly]
        context["monthly_service_costs"] = [float(m["total_cost"] or 0) for m in monthly]

        # Charts: service type distribution (row items)
        item_filter = {"record__vehicle__garage": garage} if garage else {"record__vehicle__owner": user}
        top_types_qs = (
            ServiceRecordItem.objects
            .filter(**item_filter)
            .exclude(service_type="")
            .values("service_type")
            .annotate(count=Count("id"))
            .order_by("-count")[:6]
        )
        top_type_labels = []
        top_type_counts = []
        for row in top_types_qs:
            top_type_labels.append(dict(ServiceRecord.SERVICE_CHOICES).get(row["service_type"], row["service_type"]))
            top_type_counts.append(row["count"])
        context["top_service_type_labels"] = top_type_labels
        context["top_service_type_counts"] = top_type_counts

        return context
