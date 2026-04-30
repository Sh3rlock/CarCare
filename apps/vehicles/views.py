import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from apps.core.mixins import FormConfigContextMixin
from apps.formconfig.utils import get_enabled_dynamic_modules, get_enabled_modules
from apps.garages.utils import get_active_garage
from apps.documents.models import VehicleImage

from .forms import VehicleForm
from .models import Vehicle


class OwnerQuerysetMixin:
    """Restrict every queryset to vehicles owned by the current user."""

    def get_queryset(self):
        return Vehicle.objects.filter(owner=self.request.user)


class VehicleListView(LoginRequiredMixin, OwnerQuerysetMixin, ListView):
    model = Vehicle
    template_name = "vehicles/vehicle_list.html"
    context_object_name = "vehicles"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .prefetch_related(
                Prefetch(
                    "images",
                    queryset=VehicleImage.objects.order_by("-uploaded_at"),
                    to_attr="prefetched_images",
                )
            )
        )


class VehicleDetailView(LoginRequiredMixin, OwnerQuerysetMixin, DetailView):
    model = Vehicle
    template_name = "vehicles/vehicle_detail.html"
    context_object_name = "vehicle"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        garage = self.object.garage or get_active_garage(self.request)
        context["enabled_modules"] = get_enabled_modules(garage)
        dynamic_modules = []
        for dm in get_enabled_dynamic_modules(garage):
            count = dm.records.filter(vehicle=self.object).count()
            dynamic_modules.append({"module": dm, "record_count": count})
        context["dynamic_modules"] = dynamic_modules
        context["recent_services"] = (
            self.object.service_records.prefetch_related("items").order_by("-date", "-created_at")[:5]
        )
        context["recent_quotes"] = self.object.quotes.prefetch_related("items").order_by("-date", "-created_at")[:5]
        context["recent_parts"] = (
            self.object.part_replacements.order_by("-date", "-created_at")[:5]
        )
        context["latest_mileage"] = (
            self.object.mileage_logs.order_by("-date", "-created_at").first()
        )
        context["active_insurance"] = (
            self.object.insurance_policies
            .filter(end_date__gte=datetime.date.today())
            .order_by("end_date")
            .first()
        )
        context["doc_count"] = self.object.documents.count()
        context["image_count"] = self.object.images.count()
        active_reminders = self.object.reminders.filter(is_done=False)
        context["reminder_count"] = active_reminders.count()
        context["overdue_reminder_count"] = sum(
            1 for r in active_reminders if r.is_overdue
        )
        return context


class VehicleCreateView(LoginRequiredMixin, FormConfigContextMixin, CreateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = "vehicles/vehicle_form.html"

    def get_initial(self):
        initial = super().get_initial()
        client_id = self.request.GET.get("client")
        if client_id:
            from apps.clients.models import Client

            client = Client.objects.filter(user=self.request.user, pk=client_id).first()
            if client:
                initial["client"] = client
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["garage"] = get_active_garage(self.request)
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        garage = get_active_garage(self.request)
        if garage:
            form.instance.garage = garage
        messages.success(self.request, "Vehicle added successfully.")
        return super().form_valid(form)


class VehicleUpdateView(LoginRequiredMixin, OwnerQuerysetMixin, FormConfigContextMixin, UpdateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = "vehicles/vehicle_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["garage"] = get_active_garage(self.request)
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Vehicle updated.")
        return super().form_valid(form)


class VehicleDeleteView(LoginRequiredMixin, OwnerQuerysetMixin, DeleteView):
    model = Vehicle
    template_name = "vehicles/vehicle_confirm_delete.html"
    success_url = reverse_lazy("vehicles:list")

    def form_valid(self, form):
        messages.success(self.request, "Vehicle deleted.")
        return super().form_valid(form)
