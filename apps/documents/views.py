from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, TemplateView

from apps.core.mixins import ModuleEnabledMixin, VehicleOwnerMixin

from .forms import DocumentUploadForm, ImageUploadForm
from .models import VehicleDocument, VehicleImage


class BaseVehicleMixin(ModuleEnabledMixin, VehicleOwnerMixin):
    module_key = "documents"


class DocumentListView(LoginRequiredMixin, BaseVehicleMixin, TemplateView):
    template_name = "documents/document_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vehicle = self.get_vehicle()
        context["documents"] = VehicleDocument.objects.filter(vehicle=vehicle)
        context["images"] = VehicleImage.objects.filter(vehicle=vehicle)
        return context


class DocumentUploadView(LoginRequiredMixin, BaseVehicleMixin, CreateView):
    model = VehicleDocument
    form_class = DocumentUploadForm
    template_name = "documents/document_upload.html"

    def form_valid(self, form):
        form.instance.vehicle = self.get_vehicle()
        messages.success(self.request, "Document uploaded successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("documents:list", kwargs={"vehicle_pk": self.kwargs["vehicle_pk"]})


class DocumentDeleteView(LoginRequiredMixin, BaseVehicleMixin, DeleteView):
    template_name = "documents/document_confirm_delete.html"

    def get_queryset(self):
        return VehicleDocument.objects.filter(vehicle=self.get_vehicle())

    def get_success_url(self):
        return reverse_lazy("documents:list", kwargs={"vehicle_pk": self.kwargs["vehicle_pk"]})

    def form_valid(self, form):
        messages.success(self.request, "Document deleted.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["item_label"] = "document"
        return context


class ImageUploadView(LoginRequiredMixin, BaseVehicleMixin, CreateView):
    model = VehicleImage
    form_class = ImageUploadForm
    template_name = "documents/image_upload.html"

    def form_valid(self, form):
        form.instance.vehicle = self.get_vehicle()
        messages.success(self.request, "Image uploaded successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("documents:list", kwargs={"vehicle_pk": self.kwargs["vehicle_pk"]})


class ImageDeleteView(LoginRequiredMixin, BaseVehicleMixin, DeleteView):
    template_name = "documents/document_confirm_delete.html"

    def get_queryset(self):
        return VehicleImage.objects.filter(vehicle=self.get_vehicle())

    def get_success_url(self):
        return reverse_lazy("documents:list", kwargs={"vehicle_pk": self.kwargs["vehicle_pk"]})

    def form_valid(self, form):
        messages.success(self.request, "Image deleted.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["item_label"] = "image"
        return context
