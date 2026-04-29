from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.core.mixins import FormConfigContextMixin, ModuleEnabledMixin, VehicleOwnerMixin

from .forms import MileageLogForm
from .models import MileageLog


class VehicleContextMixin(ModuleEnabledMixin, VehicleOwnerMixin):
    module_key = "mileage"

    def get_queryset(self):
        return MileageLog.objects.filter(vehicle=self.get_vehicle())


class MileageLogListView(LoginRequiredMixin, VehicleContextMixin, ListView):
    model = MileageLog
    template_name = "mileage/mileage_list.html"
    context_object_name = "logs"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        logs = list(context["logs"])

        # Attach distance driven since the previous (older) entry.
        # Queryset is ordered -date so logs[i+1] is always older.
        for i, log in enumerate(logs):
            if i < len(logs) - 1:
                log.distance_since_prev = log.odometer - logs[i + 1].odometer
            else:
                log.distance_since_prev = None

        context["logs"] = logs
        context["latest_odometer"] = logs[0].odometer if logs else None
        context["total_entries"] = len(logs)
        return context


class MileageLogCreateView(LoginRequiredMixin, VehicleContextMixin, FormConfigContextMixin, CreateView):
    model = MileageLog
    form_class = MileageLogForm
    template_name = "mileage/mileage_form.html"

    def form_valid(self, form):
        form.instance.vehicle = self.get_vehicle()
        messages.success(self.request, "Mileage entry added.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("mileage:list", kwargs={"vehicle_pk": self.kwargs["vehicle_pk"]})


class MileageLogUpdateView(LoginRequiredMixin, VehicleContextMixin, FormConfigContextMixin, UpdateView):
    model = MileageLog
    form_class = MileageLogForm
    template_name = "mileage/mileage_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Mileage entry updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("mileage:list", kwargs={"vehicle_pk": self.kwargs["vehicle_pk"]})


class MileageLogDeleteView(LoginRequiredMixin, VehicleContextMixin, DeleteView):
    model = MileageLog
    template_name = "mileage/mileage_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("mileage:list", kwargs={"vehicle_pk": self.kwargs["vehicle_pk"]})

    def form_valid(self, form):
        messages.success(self.request, "Mileage entry deleted.")
        return super().form_valid(form)
