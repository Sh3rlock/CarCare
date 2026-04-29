from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from apps.core.mixins import FormConfigContextMixin, ModuleEnabledMixin, VehicleOwnerMixin

from .forms import PartReplacementForm
from .models import PartReplacement


class VehicleContextMixin(ModuleEnabledMixin, VehicleOwnerMixin):
    module_key = "parts"

    def get_queryset(self):
        return PartReplacement.objects.filter(vehicle=self.get_vehicle())


class PartReplacementListView(LoginRequiredMixin, VehicleContextMixin, ListView):
    model = PartReplacement
    template_name = "parts/part_list.html"
    context_object_name = "parts"


class PartReplacementDetailView(LoginRequiredMixin, VehicleContextMixin, DetailView):
    model = PartReplacement
    template_name = "parts/part_detail.html"
    context_object_name = "part"


class PartReplacementCreateView(LoginRequiredMixin, VehicleContextMixin, FormConfigContextMixin, CreateView):
    model = PartReplacement
    form_class = PartReplacementForm
    template_name = "parts/part_form.html"

    def form_valid(self, form):
        form.instance.vehicle = self.get_vehicle()
        messages.success(self.request, "Part replacement recorded.")
        return super().form_valid(form)


class PartReplacementUpdateView(LoginRequiredMixin, VehicleContextMixin, FormConfigContextMixin, UpdateView):
    model = PartReplacement
    form_class = PartReplacementForm
    template_name = "parts/part_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Part replacement updated.")
        return super().form_valid(form)


class PartReplacementDeleteView(LoginRequiredMixin, VehicleContextMixin, DeleteView):
    model = PartReplacement
    template_name = "parts/part_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("parts:list", kwargs={"vehicle_pk": self.kwargs["vehicle_pk"]})

    def form_valid(self, form):
        messages.success(self.request, "Part replacement deleted.")
        return super().form_valid(form)
