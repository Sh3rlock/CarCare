from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.core.mixins import FormConfigContextMixin, ModuleEnabledMixin, VehicleOwnerMixin
from apps.vehicles.models import Vehicle

from .forms import ReminderForm
from .models import Reminder
from .utils import get_smart_alerts


class VehicleContextMixin(ModuleEnabledMixin, VehicleOwnerMixin):
    module_key = "reminders"

    def get_queryset(self):
        return Reminder.objects.filter(vehicle=self.get_vehicle())


class ReminderListView(LoginRequiredMixin, VehicleContextMixin, ListView):
    model = Reminder
    template_name = "reminders/reminder_list.html"
    context_object_name = "reminders"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["smart_alerts"] = get_smart_alerts(self.get_vehicle())
        return context


class ReminderCreateView(LoginRequiredMixin, VehicleContextMixin, FormConfigContextMixin, CreateView):
    model = Reminder
    form_class = ReminderForm
    template_name = "reminders/reminder_form.html"

    def form_valid(self, form):
        form.instance.vehicle = self.get_vehicle()
        messages.success(self.request, "Reminder added.")
        return super().form_valid(form)


class ReminderUpdateView(LoginRequiredMixin, VehicleContextMixin, FormConfigContextMixin, UpdateView):
    model = Reminder
    form_class = ReminderForm
    template_name = "reminders/reminder_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Reminder updated.")
        return super().form_valid(form)


class ReminderDeleteView(LoginRequiredMixin, VehicleContextMixin, DeleteView):
    model = Reminder
    template_name = "reminders/reminder_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("reminders:list", kwargs={"vehicle_pk": self.kwargs["vehicle_pk"]})

    def form_valid(self, form):
        messages.success(self.request, "Reminder deleted.")
        return super().form_valid(form)


class ReminderToggleView(LoginRequiredMixin, View):
    """POST-only — flips is_done without a dedicated template."""

    def post(self, request, vehicle_pk, pk):
        vehicle = get_object_or_404(Vehicle, pk=vehicle_pk, owner=request.user)
        reminder = get_object_or_404(Reminder, pk=pk, vehicle=vehicle)
        reminder.is_done = not reminder.is_done
        reminder.save(update_fields=["is_done"])
        return redirect("reminders:list", vehicle_pk=vehicle_pk)
