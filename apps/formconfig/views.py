from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView

from .forms import CustomFieldForm, DynamicModuleFieldForm, DynamicModuleForm
from .models import (
    BuiltinFieldConfig,
    CustomField,
    DynamicModule,
    DynamicModuleField,
    ModuleConfig,
)
from .utils import FORM_FIELD_DEFINITIONS, FORM_LABELS, MODULE_LABELS, PROTECTED_FIELDS


# ─────────────────────────────────────────────────────────────
#  Form Builder home
# ─────────────────────────────────────────────────────────────

@method_decorator(staff_member_required, name="dispatch")
class FormAdminListView(TemplateView):
    template_name = "formconfig/form_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        forms = []
        for key, label in FORM_LABELS.items():
            hidden_count = BuiltinFieldConfig.objects.filter(
                garage__isnull=True, form_key=key, is_visible=False
            ).count()
            custom_count = CustomField.objects.filter(
                garage__isnull=True, form_key=key, is_visible=True
            ).count()
            forms.append({
                "key": key,
                "label": label,
                "field_count": len(FORM_FIELD_DEFINITIONS[key]),
                "hidden_count": hidden_count,
                "custom_count": custom_count,
            })
        context["forms"] = forms

        disabled_keys = set(
            ModuleConfig.objects.filter(
                garage__isnull=True, is_enabled=False
            ).values_list("module_key", flat=True)
        )
        context["builtin_modules"] = [
            {"key": key, "label": label, "is_enabled": key not in disabled_keys}
            for key, label in MODULE_LABELS.items()
        ]

        context["dynamic_modules"] = DynamicModule.objects.filter(garage__isnull=True)
        return context


# ─────────────────────────────────────────────────────────────
#  Built-in module toggle
# ─────────────────────────────────────────────────────────────

@method_decorator(staff_member_required, name="dispatch")
class ToggleModuleView(View):
    def post(self, request, module_key):
        if module_key not in MODULE_LABELS:
            raise Http404
        config, _ = ModuleConfig.objects.get_or_create(
            garage=None, module_key=module_key, defaults={"is_enabled": True}
        )
        config.is_enabled = not config.is_enabled
        config.save(update_fields=["is_enabled"])
        state = "enabled" if config.is_enabled else "disabled"
        messages.success(request, f'Module "{MODULE_LABELS[module_key]}" is now {state}.')
        return redirect("formconfig:form_list")


# ─────────────────────────────────────────────────────────────
#  Dynamic module CRUD
# ─────────────────────────────────────────────────────────────

@method_decorator(staff_member_required, name="dispatch")
class DynamicModuleCreateView(View):
    template_name = "formconfig/dynamic_module_form.html"

    def get(self, request):
        return render(request, self.template_name, {"dm_form": DynamicModuleForm(), "is_new": True})

    def post(self, request):
        dm_form = DynamicModuleForm(request.POST)
        if dm_form.is_valid():
            obj = dm_form.save(commit=False)
            obj.garage = None
            obj.save()
            messages.success(request, f'Module "{obj.name}" created.')
            return redirect("formconfig:dynamic_module_fields", pk=obj.pk)
        return render(request, self.template_name, {"dm_form": dm_form, "is_new": True})


@method_decorator(staff_member_required, name="dispatch")
class DynamicModuleUpdateView(View):
    template_name = "formconfig/dynamic_module_form.html"

    def get(self, request, pk):
        obj = get_object_or_404(DynamicModule, pk=pk, garage__isnull=True)
        return render(
            request, self.template_name,
            {"dm_form": DynamicModuleForm(instance=obj), "object": obj, "is_new": False},
        )

    def post(self, request, pk):
        obj = get_object_or_404(DynamicModule, pk=pk, garage__isnull=True)
        dm_form = DynamicModuleForm(request.POST, instance=obj)
        if dm_form.is_valid():
            dm_form.save()
            messages.success(request, f'Module "{obj.name}" updated.')
            return redirect("formconfig:form_list")
        return render(
            request, self.template_name,
            {"dm_form": dm_form, "object": obj, "is_new": False},
        )


@method_decorator(staff_member_required, name="dispatch")
class DynamicModuleDeleteView(View):
    template_name = "formconfig/dynamic_module_confirm_delete.html"

    def get(self, request, pk):
        obj = get_object_or_404(DynamicModule, pk=pk, garage__isnull=True)
        return render(request, self.template_name, {"object": obj})

    def post(self, request, pk):
        obj = get_object_or_404(DynamicModule, pk=pk, garage__isnull=True)
        name = obj.name
        obj.delete()
        messages.success(request, f'Module "{name}" deleted.')
        return redirect("formconfig:form_list")


@method_decorator(staff_member_required, name="dispatch")
class ToggleDynamicModuleView(View):
    def post(self, request, pk):
        obj = get_object_or_404(DynamicModule, pk=pk, garage__isnull=True)
        obj.is_enabled = not obj.is_enabled
        obj.save(update_fields=["is_enabled"])
        state = "enabled" if obj.is_enabled else "disabled"
        messages.success(request, f'Module "{obj.name}" is now {state}.')
        return redirect("formconfig:form_list")


# ─────────────────────────────────────────────────────────────
#  Dynamic module field management
# ─────────────────────────────────────────────────────────────

@method_decorator(staff_member_required, name="dispatch")
class DynamicModuleFieldsView(View):
    template_name = "formconfig/dynamic_module_fields.html"

    def get(self, request, pk):
        module = get_object_or_404(DynamicModule, pk=pk, garage__isnull=True)
        return render(
            request, self.template_name,
            {"module": module, "fields": module.fields.order_by("position", "label")},
        )


@method_decorator(staff_member_required, name="dispatch")
class DynamicModuleFieldCreateView(View):
    template_name = "formconfig/dynamic_field_form.html"

    def get(self, request, pk):
        module = get_object_or_404(DynamicModule, pk=pk, garage__isnull=True)
        return render(
            request, self.template_name,
            {"module": module, "field_form": DynamicModuleFieldForm(), "is_new": True},
        )

    def post(self, request, pk):
        module = get_object_or_404(DynamicModule, pk=pk, garage__isnull=True)
        field_form = DynamicModuleFieldForm(request.POST)
        if field_form.is_valid():
            obj = field_form.save(commit=False)
            obj.module = module
            obj.save()
            messages.success(request, f'Field "{obj.label}" added.')
            return redirect("formconfig:dynamic_module_fields", pk=pk)
        return render(
            request, self.template_name,
            {"module": module, "field_form": field_form, "is_new": True},
        )


@method_decorator(staff_member_required, name="dispatch")
class DynamicModuleFieldUpdateView(View):
    template_name = "formconfig/dynamic_field_form.html"

    def get(self, request, pk, field_pk):
        module = get_object_or_404(DynamicModule, pk=pk, garage__isnull=True)
        field = get_object_or_404(DynamicModuleField, pk=field_pk, module=module)
        return render(
            request, self.template_name,
            {"module": module, "field_form": DynamicModuleFieldForm(instance=field),
             "object": field, "is_new": False},
        )

    def post(self, request, pk, field_pk):
        module = get_object_or_404(DynamicModule, pk=pk, garage__isnull=True)
        field = get_object_or_404(DynamicModuleField, pk=field_pk, module=module)
        field_form = DynamicModuleFieldForm(request.POST, instance=field)
        if field_form.is_valid():
            field_form.save()
            messages.success(request, f'Field "{field.label}" updated.')
            return redirect("formconfig:dynamic_module_fields", pk=pk)
        return render(
            request, self.template_name,
            {"module": module, "field_form": field_form, "object": field, "is_new": False},
        )


@method_decorator(staff_member_required, name="dispatch")
class DynamicModuleFieldDeleteView(View):
    template_name = "formconfig/dynamic_field_confirm_delete.html"

    def get(self, request, pk, field_pk):
        module = get_object_or_404(DynamicModule, pk=pk, garage__isnull=True)
        field = get_object_or_404(DynamicModuleField, pk=field_pk, module=module)
        return render(request, self.template_name, {"module": module, "object": field})

    def post(self, request, pk, field_pk):
        module = get_object_or_404(DynamicModule, pk=pk, garage__isnull=True)
        field = get_object_or_404(DynamicModuleField, pk=field_pk, module=module)
        label = field.label
        field.delete()
        messages.success(request, f'Field "{label}" deleted.')
        return redirect("formconfig:dynamic_module_fields", pk=pk)


# ─────────────────────────────────────────────────────────────
#  Built-in form field management
# ─────────────────────────────────────────────────────────────

@method_decorator(staff_member_required, name="dispatch")
class ManageFormFieldsView(View):
    template_name = "formconfig/form_fields.html"

    def _get_fields_info(self, form_key):
        protected = PROTECTED_FIELDS.get(form_key, set())
        configs = {
            c.field_name: c
            for c in BuiltinFieldConfig.objects.filter(garage__isnull=True, form_key=form_key)
        }
        result = []
        for field_name, default_label in FORM_FIELD_DEFINITIONS[form_key]:
            config = configs.get(field_name)
            result.append({
                "name": field_name,
                "default_label": default_label,
                "label_override": config.label_override if config else "",
                "is_visible": config.is_visible if config else True,
                "is_protected": field_name in protected,
            })
        return result

    def get(self, request, form_key):
        if form_key not in FORM_FIELD_DEFINITIONS:
            raise Http404
        custom_fields = CustomField.objects.filter(
            garage__isnull=True, form_key=form_key
        ).order_by("position", "label")
        return render(
            request, self.template_name,
            {
                "form_key": form_key,
                "form_label": FORM_LABELS[form_key],
                "fields_info": self._get_fields_info(form_key),
                "custom_fields": custom_fields,
            },
        )

    def post(self, request, form_key):
        if form_key not in FORM_FIELD_DEFINITIONS:
            raise Http404
        for field_name, _ in FORM_FIELD_DEFINITIONS[form_key]:
            label_override = request.POST.get(f"label_{field_name}", "").strip()
            BuiltinFieldConfig.objects.update_or_create(
                garage=None,
                form_key=form_key,
                field_name=field_name,
                defaults={"label_override": label_override},
            )
        messages.success(request, "Labels saved.")
        return redirect("formconfig:form_fields", form_key=form_key)


@method_decorator(staff_member_required, name="dispatch")
class ToggleFieldVisibilityView(View):
    def post(self, request, form_key, field_name):
        if form_key not in FORM_FIELD_DEFINITIONS:
            raise Http404
        known = {name for name, _ in FORM_FIELD_DEFINITIONS[form_key]}
        if field_name not in known:
            raise Http404
        protected = PROTECTED_FIELDS.get(form_key, set())
        if field_name in protected:
            messages.warning(request, f'"{field_name}" is a required field and cannot be hidden.')
            return redirect("formconfig:form_fields", form_key=form_key)
        config, _ = BuiltinFieldConfig.objects.get_or_create(
            garage=None,
            form_key=form_key,
            field_name=field_name,
            defaults={"is_visible": True},
        )
        config.is_visible = not config.is_visible
        config.save(update_fields=["is_visible"])
        state = "shown" if config.is_visible else "hidden"
        messages.success(request, f'Field "{field_name}" is now {state}.')
        return redirect("formconfig:form_fields", form_key=form_key)


@method_decorator(staff_member_required, name="dispatch")
class CustomFieldCreateView(View):
    template_name = "formconfig/custom_field_form.html"

    def get(self, request, form_key):
        if form_key not in FORM_FIELD_DEFINITIONS:
            raise Http404
        return render(
            request, self.template_name,
            {"form_key": form_key, "form_label": FORM_LABELS[form_key],
             "cf_form": CustomFieldForm(), "is_new": True},
        )

    def post(self, request, form_key):
        if form_key not in FORM_FIELD_DEFINITIONS:
            raise Http404
        cf_form = CustomFieldForm(request.POST)
        if cf_form.is_valid():
            obj = cf_form.save(commit=False)
            obj.form_key = form_key
            obj.garage = None
            obj.save()
            messages.success(request, f'Custom field "{obj.label}" added.')
            return redirect("formconfig:form_fields", form_key=form_key)
        return render(
            request, self.template_name,
            {"form_key": form_key, "form_label": FORM_LABELS[form_key],
             "cf_form": cf_form, "is_new": True},
        )


@method_decorator(staff_member_required, name="dispatch")
class CustomFieldUpdateView(View):
    template_name = "formconfig/custom_field_form.html"

    def get(self, request, form_key, pk):
        obj = get_object_or_404(CustomField, pk=pk, form_key=form_key, garage__isnull=True)
        return render(
            request, self.template_name,
            {"form_key": form_key, "form_label": FORM_LABELS[form_key],
             "cf_form": CustomFieldForm(instance=obj), "object": obj, "is_new": False},
        )

    def post(self, request, form_key, pk):
        obj = get_object_or_404(CustomField, pk=pk, form_key=form_key, garage__isnull=True)
        cf_form = CustomFieldForm(request.POST, instance=obj)
        if cf_form.is_valid():
            cf_form.save()
            messages.success(request, f'Custom field "{obj.label}" updated.')
            return redirect("formconfig:form_fields", form_key=form_key)
        return render(
            request, self.template_name,
            {"form_key": form_key, "form_label": FORM_LABELS[form_key],
             "cf_form": cf_form, "object": obj, "is_new": False},
        )


@method_decorator(staff_member_required, name="dispatch")
class CustomFieldDeleteView(View):
    template_name = "formconfig/custom_field_confirm_delete.html"

    def get(self, request, form_key, pk):
        obj = get_object_or_404(CustomField, pk=pk, form_key=form_key, garage__isnull=True)
        return render(
            request, self.template_name,
            {"form_key": form_key, "form_label": FORM_LABELS[form_key], "object": obj},
        )

    def post(self, request, form_key, pk):
        obj = get_object_or_404(CustomField, pk=pk, form_key=form_key, garage__isnull=True)
        label = obj.label
        obj.delete()
        messages.success(request, f'Custom field "{label}" deleted.')
        return redirect("formconfig:form_fields", form_key=form_key)
