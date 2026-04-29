from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views import View

from apps.catalog.utils import get_active_models
from apps.garages.models import GarageMembership
from apps.garages.utils import get_active_garage

from .forms import CarMakeForm, CarModelForm, DropdownChoiceForm
from .models import DROPDOWN_LIST_CHOICES, CarMake, CarModel, DropdownChoice


class CatalogAdminMixin(UserPassesTestMixin):
    """Allow staff users and garage owners."""
    def test_func(self):
        user = self.request.user
        return user.is_staff or GarageMembership.objects.filter(
            user=user, role=GarageMembership.Role.OWNER
        ).exists()

_DROPDOWN_LABELS = dict(DROPDOWN_LIST_CHOICES)


def _get_dropdown_return_url(list_key):
    if list_key == "consumables":
        return "catalog:consumables_list"
    if list_key == "service_type":
        return "catalog:service_types_list"
    return "catalog:dropdown_list"


def _build_dropdown_value(list_key, label, fallback_value=""):
    if list_key == "consumables":
        return slugify(label).replace("-", "_")[:50]
    return (fallback_value or label)[:50]


# ─── API ──────────────────────────────────────────────────────────────────────

def models_for_make_api(request):
    """Returns JSON list of model names for a given make name, scoped to active garage."""
    make_name = request.GET.get("make", "").strip()
    if not make_name:
        return JsonResponse([], safe=False)
    garage = get_active_garage(request)
    names = get_active_models(make_name, garage)
    return JsonResponse(names, safe=False)


@login_required
def make_quick_add_api(request):
    """Quick-create a CarMake in the global catalog. POST only."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    name = request.POST.get("name", "").strip()
    if not name:
        return JsonResponse({"errors": {"name": ["Make name is required."]}}, status=400)
    obj, created = CarMake.objects.get_or_create(name=name, garage=None, defaults={"is_active": True})
    return JsonResponse({"name": obj.name, "created": created})


@login_required
def model_quick_add_api(request):
    """Quick-create a CarModel in the global catalog. POST only."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    make_name = request.POST.get("make", "").strip()
    name = request.POST.get("name", "").strip()
    errors = {}
    if not make_name:
        errors["make"] = ["Make is required."]
    if not name:
        errors["name"] = ["Model name is required."]
    if errors:
        return JsonResponse({"errors": errors}, status=400)
    make, _ = CarMake.objects.get_or_create(name=make_name, garage=None, defaults={"is_active": True})
    obj, created = CarModel.objects.get_or_create(make=make, name=name, garage=None, defaults={"is_active": True})
    return JsonResponse({"name": obj.name, "make": make.name, "created": created})


@login_required
def dropdown_choice_quick_add_api(request, list_key):
    """Quick-create a dropdown choice for a catalog-backed select. POST only."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    if list_key not in _DROPDOWN_LABELS:
        raise Http404

    label = request.POST.get("label", "").strip()
    value = request.POST.get("value", "").strip()
    errors = {}
    if not label:
        errors["label"] = ["Label is required."]

    value = _build_dropdown_value(list_key, label, value)
    value = value[:50]
    if not value:
        errors["value"] = ["Value is required."]

    if errors:
        return JsonResponse({"errors": errors}, status=400)

    obj, created = DropdownChoice.objects.get_or_create(
        list_key=list_key,
        value=value,
        garage=None,
        defaults={"label": label, "is_active": True},
    )
    if not created and obj.label != label:
        obj.label = label
        obj.save(update_fields=["label"])

    return JsonResponse(
        {"value": obj.value, "label": obj.label, "created": created, "list_key": list_key}
    )


# ─── Makes ────────────────────────────────────────────────────────────────────

class CarMakeListView(CatalogAdminMixin, View):
    template_name = "catalog/make_list.html"

    def get(self, request):
        makes = CarMake.objects.all()
        return render(request, self.template_name, {"makes": makes})


class CarMakeCreateView(CatalogAdminMixin, View):
    template_name = "catalog/make_form.html"

    def get(self, request):
        return render(request, self.template_name, {"form": CarMakeForm(), "is_new": True})

    def post(self, request):
        form = CarMakeForm(request.POST)
        if form.is_valid():
            obj = form.save()
            messages.success(request, f'"{obj.name}" added.')
            return redirect("catalog:make_list")
        return render(request, self.template_name, {"form": form, "is_new": True})


class CarMakeUpdateView(CatalogAdminMixin, View):
    template_name = "catalog/make_form.html"

    def get(self, request, pk):
        obj = get_object_or_404(CarMake, pk=pk)
        return render(request, self.template_name, {"form": CarMakeForm(instance=obj), "object": obj, "is_new": False})

    def post(self, request, pk):
        obj = get_object_or_404(CarMake, pk=pk)
        form = CarMakeForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{obj.name}" updated.')
            return redirect("catalog:make_list")
        return render(request, self.template_name, {"form": form, "object": obj, "is_new": False})


class CarMakeDeleteView(CatalogAdminMixin, View):
    template_name = "catalog/make_confirm_delete.html"

    def get(self, request, pk):
        obj = get_object_or_404(CarMake, pk=pk)
        return render(request, self.template_name, {"object": obj})

    def post(self, request, pk):
        obj = get_object_or_404(CarMake, pk=pk)
        name = obj.name
        obj.delete()
        messages.success(request, f'"{name}" deleted.')
        return redirect("catalog:make_list")


# ─── Models ───────────────────────────────────────────────────────────────────

class CarModelListView(CatalogAdminMixin, View):
    template_name = "catalog/model_list.html"

    def get(self, request, make_pk):
        make = get_object_or_404(CarMake, pk=make_pk)
        return render(request, self.template_name, {"make": make, "car_models": make.car_models.all()})


class CarModelCreateView(CatalogAdminMixin, View):
    template_name = "catalog/model_form.html"

    def get(self, request, make_pk):
        make = get_object_or_404(CarMake, pk=make_pk)
        return render(request, self.template_name, {"make": make, "form": CarModelForm(), "is_new": True})

    def post(self, request, make_pk):
        make = get_object_or_404(CarMake, pk=make_pk)
        form = CarModelForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.make = make
            obj.save()
            messages.success(request, f'"{obj.name}" added to {make.name}.')
            return redirect("catalog:model_list", make_pk=make_pk)
        return render(request, self.template_name, {"make": make, "form": form, "is_new": True})


class CarModelUpdateView(CatalogAdminMixin, View):
    template_name = "catalog/model_form.html"

    def get(self, request, make_pk, pk):
        make = get_object_or_404(CarMake, pk=make_pk)
        obj = get_object_or_404(CarModel, pk=pk, make=make)
        return render(request, self.template_name, {"make": make, "form": CarModelForm(instance=obj), "object": obj, "is_new": False})

    def post(self, request, make_pk, pk):
        make = get_object_or_404(CarMake, pk=make_pk)
        obj = get_object_or_404(CarModel, pk=pk, make=make)
        form = CarModelForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{obj.name}" updated.')
            return redirect("catalog:model_list", make_pk=make_pk)
        return render(request, self.template_name, {"make": make, "form": form, "object": obj, "is_new": False})


class CarModelDeleteView(CatalogAdminMixin, View):
    template_name = "catalog/model_confirm_delete.html"

    def get(self, request, make_pk, pk):
        make = get_object_or_404(CarMake, pk=make_pk)
        obj = get_object_or_404(CarModel, pk=pk, make=make)
        return render(request, self.template_name, {"make": make, "object": obj})

    def post(self, request, make_pk, pk):
        make = get_object_or_404(CarMake, pk=make_pk)
        obj = get_object_or_404(CarModel, pk=pk, make=make)
        name = obj.name
        obj.delete()
        messages.success(request, f'"{name}" deleted from {make.name}.')
        return redirect("catalog:model_list", make_pk=make_pk)


# ─── Dropdown Choices ─────────────────────────────────────────────────────────

class DropdownListView(CatalogAdminMixin, View):
    template_name = "catalog/dropdown_list.html"

    def _get_list_context(self, list_key=None):
        selected_keys = [list_key] if list_key else ["fuel_type", "transmission"]
        lists = [
            {"key": key, "label": label, "choices": DropdownChoice.objects.filter(list_key=key)}
            for key, label in DROPDOWN_LIST_CHOICES
            if key in selected_keys
        ]
        active_tab = "dropdowns"
        if list_key == "service_type":
            active_tab = "service_types"
        elif list_key == "consumables":
            active_tab = "consumables"
        return {
            "lists": lists,
            "active_tab": active_tab,
        }

    def get(self, request):
        return render(request, self.template_name, self._get_list_context())


class ConsumablesListView(DropdownListView):
    def get(self, request):
        return render(request, self.template_name, self._get_list_context("consumables"))


class ServiceTypesListView(DropdownListView):
    def get(self, request):
        return render(request, self.template_name, self._get_list_context("service_type"))


class DropdownChoiceCreateView(CatalogAdminMixin, View):
    template_name = "catalog/dropdown_choice_form.html"

    def _get_label(self, list_key):
        if list_key not in _DROPDOWN_LABELS:
            raise Http404
        return _DROPDOWN_LABELS[list_key]

    def get(self, request, list_key):
        label = self._get_label(list_key)
        return render(
            request,
            self.template_name,
            {
                "form": DropdownChoiceForm(list_key=list_key),
                "show_value_field": list_key != "consumables",
                "list_key": list_key,
                "list_label": label,
                "is_new": True,
                "return_url": _get_dropdown_return_url(list_key),
            },
        )

    def post(self, request, list_key):
        label = self._get_label(list_key)
        form = DropdownChoiceForm(request.POST, list_key=list_key)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.list_key = list_key
            obj.save()
            messages.success(request, f'"{obj.label}" added.')
            return redirect(_get_dropdown_return_url(list_key))
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "show_value_field": list_key != "consumables",
                "list_key": list_key,
                "list_label": label,
                "is_new": True,
                "return_url": _get_dropdown_return_url(list_key),
            },
        )


class DropdownChoiceUpdateView(CatalogAdminMixin, View):
    template_name = "catalog/dropdown_choice_form.html"

    def get(self, request, list_key, pk):
        obj = get_object_or_404(DropdownChoice, pk=pk, list_key=list_key)
        label = _DROPDOWN_LABELS.get(list_key, list_key)
        return render(
            request,
            self.template_name,
            {
                "form": DropdownChoiceForm(instance=obj, list_key=list_key),
                "show_value_field": list_key != "consumables",
                "list_key": list_key,
                "list_label": label,
                "object": obj,
                "is_new": False,
                "return_url": _get_dropdown_return_url(list_key),
            },
        )

    def post(self, request, list_key, pk):
        obj = get_object_or_404(DropdownChoice, pk=pk, list_key=list_key)
        label = _DROPDOWN_LABELS.get(list_key, list_key)
        form = DropdownChoiceForm(request.POST, instance=obj, list_key=list_key)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{obj.label}" updated.')
            return redirect(_get_dropdown_return_url(list_key))
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "show_value_field": list_key != "consumables",
                "list_key": list_key,
                "list_label": label,
                "object": obj,
                "is_new": False,
                "return_url": _get_dropdown_return_url(list_key),
            },
        )


class DropdownChoiceDeleteView(CatalogAdminMixin, View):
    template_name = "catalog/dropdown_choice_confirm_delete.html"

    def get(self, request, list_key, pk):
        obj = get_object_or_404(DropdownChoice, pk=pk, list_key=list_key)
        return render(
            request,
            self.template_name,
            {
                "object": obj,
                "list_key": list_key,
                "list_label": _DROPDOWN_LABELS.get(list_key, list_key),
                "return_url": _get_dropdown_return_url(list_key),
            },
        )

    def post(self, request, list_key, pk):
        obj = get_object_or_404(DropdownChoice, pk=pk, list_key=list_key)
        lbl = obj.label
        obj.delete()
        messages.success(request, f'"{lbl}" deleted.')
        return redirect(_get_dropdown_return_url(list_key))
