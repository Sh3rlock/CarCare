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

from .forms import InsurancePolicyForm
from .models import InsurancePolicy


class VehicleContextMixin(ModuleEnabledMixin, VehicleOwnerMixin):
    module_key = "insurance"

    def get_queryset(self):
        return InsurancePolicy.objects.filter(vehicle=self.get_vehicle())


class InsurancePolicyListView(LoginRequiredMixin, VehicleContextMixin, ListView):
    model = InsurancePolicy
    template_name = "insurance/insurance_list.html"
    context_object_name = "policies"


class InsurancePolicyDetailView(LoginRequiredMixin, VehicleContextMixin, DetailView):
    model = InsurancePolicy
    template_name = "insurance/insurance_detail.html"
    context_object_name = "policy"


class InsurancePolicyCreateView(LoginRequiredMixin, VehicleContextMixin, FormConfigContextMixin, CreateView):
    model = InsurancePolicy
    form_class = InsurancePolicyForm
    template_name = "insurance/insurance_form.html"

    def form_valid(self, form):
        form.instance.vehicle = self.get_vehicle()
        messages.success(self.request, "Insurance policy added.")
        return super().form_valid(form)


class InsurancePolicyUpdateView(LoginRequiredMixin, VehicleContextMixin, FormConfigContextMixin, UpdateView):
    model = InsurancePolicy
    form_class = InsurancePolicyForm
    template_name = "insurance/insurance_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Insurance policy updated.")
        return super().form_valid(form)


class InsurancePolicyDeleteView(LoginRequiredMixin, VehicleContextMixin, DeleteView):
    model = InsurancePolicy
    template_name = "insurance/insurance_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy(
            "insurance:list", kwargs={"vehicle_pk": self.kwargs["vehicle_pk"]}
        )

    def form_valid(self, form):
        messages.success(self.request, "Insurance policy deleted.")
        return super().form_valid(form)
