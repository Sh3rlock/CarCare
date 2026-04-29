from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView

from apps.formconfig.models import (
    BuiltinFieldConfig,
    CustomField,
    DynamicModule,
    DynamicModuleField,
    ModuleConfig,
)
from apps.formconfig.utils import (
    FORM_FIELD_DEFINITIONS,
    FORM_LABELS,
    MODULE_LABELS,
    PROTECTED_FIELDS,
)

from .forms import (
    GarageCreateMemberForm,
    GarageCustomFieldForm,
    GarageDynamicModuleFieldForm,
    GarageDynamicModuleForm,
    GarageForm,
    GarageInviteForm,
)
from .mixins import GarageAdminMixin, GarageOwnerMixin, GarageResolveMixin
from .models import Garage, GarageMembership
from . import permissions as garage_perms

User = get_user_model()


# ─────────────────────────────────────────────────────────────
#  Garage CRUD
# ─────────────────────────────────────────────────────────────

class GarageListView(LoginRequiredMixin, ListView):
    template_name = "garages/garage_list.html"
    context_object_name = "garages"

    def get_queryset(self):
        return Garage.objects.filter(memberships__user=self.request.user).distinct()


class GarageCreateView(LoginRequiredMixin, View):
    template_name = "garages/garage_form.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, self.template_name, {"form": GarageForm(), "is_new": True})

    def post(self, request):
        form = GarageForm(request.POST)
        if form.is_valid():
            garage = form.save(commit=False)
            garage.owner = request.user
            if not garage.slug:
                garage.slug = slugify(garage.name)
            garage.save()
            GarageMembership.objects.create(
                user=request.user, garage=garage, role=GarageMembership.Role.OWNER
            )
            messages.success(request, f'Garage "{garage.name}" created.')
            return redirect("garages:dashboard", garage_slug=garage.slug)
        return render(request, self.template_name, {"form": form, "is_new": True})


class GarageUpdateView(LoginRequiredMixin, GarageOwnerMixin, View):
    template_name = "garages/garage_form.html"

    def get(self, request, garage_slug):
        garage = self.get_garage()
        return render(request, self.template_name, {"form": GarageForm(instance=garage), "is_new": False, "garage": garage})

    def post(self, request, garage_slug):
        garage = self.get_garage()
        form = GarageForm(request.POST, instance=garage)
        if form.is_valid():
            form.save()
            messages.success(request, "Garage updated.")
            return redirect("garages:dashboard", garage_slug=garage.slug)
        return render(request, self.template_name, {"form": form, "is_new": False, "garage": garage})


class GarageDeleteView(LoginRequiredMixin, GarageOwnerMixin, View):
    template_name = "garages/garage_confirm_delete.html"

    def get(self, request, garage_slug):
        return render(request, self.template_name, {"garage": self.get_garage()})

    def post(self, request, garage_slug):
        garage = self.get_garage()
        name = garage.name
        garage.delete()
        messages.success(request, f'Garage "{name}" deleted.')
        return redirect("garages:list")


# ─────────────────────────────────────────────────────────────
#  Garage dashboard & vehicle list
# ─────────────────────────────────────────────────────────────

class GarageDashboardView(LoginRequiredMixin, GarageResolveMixin, View):
    template_name = "garages/garage_dashboard.html"

    def get(self, request, garage_slug):
        garage = self.get_garage()
        membership = GarageMembership.objects.filter(user=request.user, garage=garage).first()
        context = {
            "garage": garage,
            "membership": membership,
            "vehicle_count": garage.vehicles.count(),
            "member_count": garage.memberships.count(),
            "can_admin": garage_perms.can_manage_members(request.user, garage),
            "can_manage": garage_perms.can_manage_garage(request.user, garage),
        }
        return render(request, self.template_name, context)


class GarageVehicleListView(LoginRequiredMixin, GarageResolveMixin, View):
    template_name = "garages/garage_vehicles.html"

    def get(self, request, garage_slug):
        garage = self.get_garage()
        vehicles = garage.vehicles.select_related("client").order_by("-created_at")
        return render(request, self.template_name, {"garage": garage, "vehicles": vehicles})


# ─────────────────────────────────────────────────────────────
#  Member management
# ─────────────────────────────────────────────────────────────

class GarageMemberListView(LoginRequiredMixin, GarageAdminMixin, View):
    template_name = "garages/garage_members.html"

    def get(self, request, garage_slug):
        garage = self.get_garage()
        memberships = garage.memberships.select_related("user").order_by("role", "user__username")
        return render(
            request, self.template_name,
            {
                "garage": garage,
                "memberships": memberships,
                "invite_form": GarageInviteForm(),
                "create_member_form": GarageCreateMemberForm(),
            },
        )

    def post(self, request, garage_slug):
        garage = self.get_garage()
        action = request.POST.get("action")
        if action == "create_member":
            create_member_form = GarageCreateMemberForm(request.POST)
            invite_form = GarageInviteForm()
            if create_member_form.is_valid():
                username = create_member_form.cleaned_data["username"]
                email = create_member_form.cleaned_data["email"]
                role = create_member_form.cleaned_data["role"]
                if User.objects.filter(username__iexact=username).exists():
                    create_member_form.add_error("username", "A user with this username already exists.")
                elif email and User.objects.filter(email__iexact=email).exists():
                    create_member_form.add_error("email", "A user with this email already exists.")
                else:
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=create_member_form.cleaned_data["password"],
                        first_name=create_member_form.cleaned_data["first_name"],
                        last_name=create_member_form.cleaned_data["last_name"],
                    )
                    GarageMembership.objects.create(user=user, garage=garage, role=role)
                    messages.success(
                        request,
                        f'User "{user.username}" created and added as {role}. They can change password in Profile.',
                    )
                    return redirect("garages:members", garage_slug=garage_slug)
            memberships = garage.memberships.select_related("user").order_by("role", "user__username")
            return render(
                request, self.template_name,
                {
                    "garage": garage,
                    "memberships": memberships,
                    "invite_form": invite_form,
                    "create_member_form": create_member_form,
                },
            )

        invite_form = GarageInviteForm(request.POST)
        create_member_form = GarageCreateMemberForm()
        if invite_form.is_valid():
            query = invite_form.cleaned_data["username_or_email"]
            role = invite_form.cleaned_data["role"]
            user = User.objects.filter(Q(username=query) | Q(email=query)).first()
            if not user:
                messages.error(request, f'No user found matching "{query}".')
            elif GarageMembership.objects.filter(user=user, garage=garage).exists():
                messages.warning(request, f"{user.username} is already a member.")
            else:
                GarageMembership.objects.create(user=user, garage=garage, role=role)
                messages.success(request, f"{user.username} added as {role}.")
            return redirect("garages:members", garage_slug=garage_slug)
        memberships = garage.memberships.select_related("user").order_by("role", "user__username")
        return render(
            request, self.template_name,
            {
                "garage": garage,
                "memberships": memberships,
                "invite_form": invite_form,
                "create_member_form": create_member_form,
            },
        )


class GarageChangeMemberRoleView(LoginRequiredMixin, GarageAdminMixin, View):
    def post(self, request, garage_slug, pk):
        garage = self.get_garage()
        membership = get_object_or_404(GarageMembership, pk=pk, garage=garage)
        if membership.role == GarageMembership.Role.OWNER:
            messages.error(request, "Cannot change the owner's role.")
            return redirect("garages:members", garage_slug=garage_slug)
        new_role = request.POST.get("role")
        if new_role not in dict(GarageMembership.Role.choices):
            messages.error(request, "Invalid role.")
            return redirect("garages:members", garage_slug=garage_slug)
        membership.role = new_role
        membership.save(update_fields=["role"])
        messages.success(request, f"Role updated to {membership.get_role_display()}.")
        return redirect("garages:members", garage_slug=garage_slug)


class GarageRemoveMemberView(LoginRequiredMixin, GarageAdminMixin, View):
    def post(self, request, garage_slug, pk):
        garage = self.get_garage()
        membership = get_object_or_404(GarageMembership, pk=pk, garage=garage)
        if membership.role == GarageMembership.Role.OWNER:
            messages.error(request, "The owner cannot be removed.")
            return redirect("garages:members", garage_slug=garage_slug)
        if membership.user == request.user:
            messages.error(request, "You cannot remove yourself.")
            return redirect("garages:members", garage_slug=garage_slug)
        username = membership.user.username
        membership.delete()
        messages.success(request, f"{username} removed from garage.")
        return redirect("garages:members", garage_slug=garage_slug)


# ─────────────────────────────────────────────────────────────
#  Per-garage settings (form builder)
# ─────────────────────────────────────────────────────────────

class GarageSettingsView(LoginRequiredMixin, GarageAdminMixin, View):
    template_name = "garages/settings/settings_list.html"

    def get(self, request, garage_slug):
        garage = self.get_garage()

        forms_info = []
        for key, label in FORM_LABELS.items():
            hidden = BuiltinFieldConfig.objects.filter(
                garage=garage, form_key=key, is_visible=False
            ).count()
            custom = CustomField.objects.filter(
                garage=garage, form_key=key, is_visible=True
            ).count()
            forms_info.append({"key": key, "label": label, "hidden_count": hidden, "custom_count": custom})

        disabled_keys = set(
            ModuleConfig.objects.filter(
                garage=garage, is_enabled=False
            ).values_list("module_key", flat=True)
        )
        # Merge global disabled into display (global can also disable for this garage)
        global_disabled = set(
            ModuleConfig.objects.filter(
                garage__isnull=True, is_enabled=False
            ).values_list("module_key", flat=True)
        )
        modules_info = []
        for key, label in MODULE_LABELS.items():
            garage_override = ModuleConfig.objects.filter(garage=garage, module_key=key).first()
            if garage_override is not None:
                is_enabled = garage_override.is_enabled
            else:
                is_enabled = key not in global_disabled
            modules_info.append({"key": key, "label": label, "is_enabled": is_enabled})

        dynamic_modules = DynamicModule.objects.filter(garage=garage)
        return render(request, self.template_name, {
            "garage": garage,
            "forms_info": forms_info,
            "modules_info": modules_info,
            "dynamic_modules": dynamic_modules,
        })


class GarageToggleModuleView(LoginRequiredMixin, GarageAdminMixin, View):
    def post(self, request, garage_slug, module_key):
        if module_key not in MODULE_LABELS:
            from django.http import Http404
            raise Http404
        garage = self.get_garage()
        config, _ = ModuleConfig.objects.get_or_create(
            garage=garage, module_key=module_key, defaults={"is_enabled": True}
        )
        config.is_enabled = not config.is_enabled
        config.save(update_fields=["is_enabled"])
        state = "enabled" if config.is_enabled else "disabled"
        messages.success(request, f'Module "{MODULE_LABELS[module_key]}" is now {state} for this garage.')
        return redirect("garages:settings", garage_slug=garage_slug)


# ─── Per-garage form fields ───────────────────────────────────

class GarageFormFieldsView(LoginRequiredMixin, GarageAdminMixin, View):
    template_name = "garages/settings/form_fields.html"

    def _get_fields_info(self, form_key, garage):
        protected = PROTECTED_FIELDS.get(form_key, set())
        global_configs = {
            c.field_name: c
            for c in BuiltinFieldConfig.objects.filter(garage__isnull=True, form_key=form_key)
        }
        garage_configs = {
            c.field_name: c
            for c in BuiltinFieldConfig.objects.filter(garage=garage, form_key=form_key)
        }
        result = []
        for field_name, default_label in FORM_FIELD_DEFINITIONS[form_key]:
            garage_cfg = garage_configs.get(field_name)
            global_cfg = global_configs.get(field_name)
            effective = garage_cfg or global_cfg
            result.append({
                "name": field_name,
                "default_label": default_label,
                "label_override": garage_cfg.label_override if garage_cfg else "",
                "is_visible": effective.is_visible if effective else True,
                "is_protected": field_name in protected,
                "has_override": garage_cfg is not None,
            })
        return result

    def get(self, request, garage_slug, form_key):
        if form_key not in FORM_FIELD_DEFINITIONS:
            from django.http import Http404
            raise Http404
        garage = self.get_garage()
        custom_fields = CustomField.objects.filter(
            garage=garage, form_key=form_key
        ).order_by("position", "label")
        return render(request, self.template_name, {
            "garage": garage,
            "form_key": form_key,
            "form_label": FORM_LABELS[form_key],
            "fields_info": self._get_fields_info(form_key, garage),
            "custom_fields": custom_fields,
        })

    def post(self, request, garage_slug, form_key):
        if form_key not in FORM_FIELD_DEFINITIONS:
            from django.http import Http404
            raise Http404
        garage = self.get_garage()
        for field_name, _ in FORM_FIELD_DEFINITIONS[form_key]:
            label_override = request.POST.get(f"label_{field_name}", "").strip()
            BuiltinFieldConfig.objects.update_or_create(
                garage=garage,
                form_key=form_key,
                field_name=field_name,
                defaults={"label_override": label_override},
            )
        messages.success(request, "Labels saved.")
        return redirect("garages:form_fields", garage_slug=garage_slug, form_key=form_key)


class GarageToggleFieldView(LoginRequiredMixin, GarageAdminMixin, View):
    def post(self, request, garage_slug, form_key, field_name):
        if form_key not in FORM_FIELD_DEFINITIONS:
            from django.http import Http404
            raise Http404
        known = {name for name, _ in FORM_FIELD_DEFINITIONS[form_key]}
        if field_name not in known:
            from django.http import Http404
            raise Http404
        protected = PROTECTED_FIELDS.get(form_key, set())
        if field_name in protected:
            messages.warning(request, f'"{field_name}" is a required field and cannot be hidden.')
            return redirect("garages:form_fields", garage_slug=garage_slug, form_key=form_key)
        garage = self.get_garage()
        config, _ = BuiltinFieldConfig.objects.get_or_create(
            garage=garage, form_key=form_key, field_name=field_name,
            defaults={"is_visible": True},
        )
        config.is_visible = not config.is_visible
        config.save(update_fields=["is_visible"])
        state = "shown" if config.is_visible else "hidden"
        messages.success(request, f'Field "{field_name}" is now {state} for this garage.')
        return redirect("garages:form_fields", garage_slug=garage_slug, form_key=form_key)


# ─── Per-garage custom fields ─────────────────────────────────

class GarageCustomFieldCreateView(LoginRequiredMixin, GarageAdminMixin, View):
    template_name = "garages/settings/custom_field_form.html"

    def get(self, request, garage_slug, form_key):
        if form_key not in FORM_FIELD_DEFINITIONS:
            from django.http import Http404
            raise Http404
        return render(request, self.template_name, {
            "garage": self.get_garage(), "form_key": form_key,
            "form_label": FORM_LABELS[form_key], "cf_form": GarageCustomFieldForm(), "is_new": True,
        })

    def post(self, request, garage_slug, form_key):
        if form_key not in FORM_FIELD_DEFINITIONS:
            from django.http import Http404
            raise Http404
        garage = self.get_garage()
        cf_form = GarageCustomFieldForm(request.POST)
        if cf_form.is_valid():
            obj = cf_form.save(commit=False)
            obj.form_key = form_key
            obj.garage = garage
            obj.save()
            messages.success(request, f'Custom field "{obj.label}" added.')
            return redirect("garages:form_fields", garage_slug=garage_slug, form_key=form_key)
        return render(request, self.template_name, {
            "garage": garage, "form_key": form_key,
            "form_label": FORM_LABELS[form_key], "cf_form": cf_form, "is_new": True,
        })


class GarageCustomFieldUpdateView(LoginRequiredMixin, GarageAdminMixin, View):
    template_name = "garages/settings/custom_field_form.html"

    def _get_field(self, garage, form_key, pk):
        return get_object_or_404(CustomField, pk=pk, garage=garage, form_key=form_key)

    def get(self, request, garage_slug, form_key, pk):
        garage = self.get_garage()
        obj = self._get_field(garage, form_key, pk)
        return render(request, self.template_name, {
            "garage": garage, "form_key": form_key, "form_label": FORM_LABELS[form_key],
            "cf_form": GarageCustomFieldForm(instance=obj), "object": obj, "is_new": False,
        })

    def post(self, request, garage_slug, form_key, pk):
        garage = self.get_garage()
        obj = self._get_field(garage, form_key, pk)
        cf_form = GarageCustomFieldForm(request.POST, instance=obj)
        if cf_form.is_valid():
            cf_form.save()
            messages.success(request, f'Custom field "{obj.label}" updated.')
            return redirect("garages:form_fields", garage_slug=garage_slug, form_key=form_key)
        return render(request, self.template_name, {
            "garage": garage, "form_key": form_key, "form_label": FORM_LABELS[form_key],
            "cf_form": cf_form, "object": obj, "is_new": False,
        })


class GarageCustomFieldDeleteView(LoginRequiredMixin, GarageAdminMixin, View):
    template_name = "garages/settings/custom_field_confirm_delete.html"

    def _get_field(self, garage, form_key, pk):
        return get_object_or_404(CustomField, pk=pk, garage=garage, form_key=form_key)

    def get(self, request, garage_slug, form_key, pk):
        garage = self.get_garage()
        obj = self._get_field(garage, form_key, pk)
        return render(request, self.template_name, {
            "garage": garage, "form_key": form_key,
            "form_label": FORM_LABELS[form_key], "object": obj,
        })

    def post(self, request, garage_slug, form_key, pk):
        garage = self.get_garage()
        obj = self._get_field(garage, form_key, pk)
        label = obj.label
        obj.delete()
        messages.success(request, f'Custom field "{label}" deleted.')
        return redirect("garages:form_fields", garage_slug=garage_slug, form_key=form_key)


# ─── Per-garage dynamic modules ───────────────────────────────

class GarageDynamicModuleCreateView(LoginRequiredMixin, GarageAdminMixin, View):
    template_name = "garages/settings/dynamic_module_form.html"

    def get(self, request, garage_slug):
        return render(request, self.template_name, {
            "garage": self.get_garage(), "dm_form": GarageDynamicModuleForm(), "is_new": True,
        })

    def post(self, request, garage_slug):
        garage = self.get_garage()
        dm_form = GarageDynamicModuleForm(request.POST)
        if dm_form.is_valid():
            obj = dm_form.save(commit=False)
            obj.garage = garage
            obj.save()
            messages.success(request, f'Module "{obj.name}" created.')
            return redirect("garages:dynamic_module_fields", garage_slug=garage_slug, pk=obj.pk)
        return render(request, self.template_name, {
            "garage": garage, "dm_form": dm_form, "is_new": True,
        })


class GarageDynamicModuleUpdateView(LoginRequiredMixin, GarageAdminMixin, View):
    template_name = "garages/settings/dynamic_module_form.html"

    def get(self, request, garage_slug, pk):
        garage = self.get_garage()
        obj = get_object_or_404(DynamicModule, pk=pk, garage=garage)
        return render(request, self.template_name, {
            "garage": garage, "dm_form": GarageDynamicModuleForm(instance=obj),
            "object": obj, "is_new": False,
        })

    def post(self, request, garage_slug, pk):
        garage = self.get_garage()
        obj = get_object_or_404(DynamicModule, pk=pk, garage=garage)
        dm_form = GarageDynamicModuleForm(request.POST, instance=obj)
        if dm_form.is_valid():
            dm_form.save()
            messages.success(request, f'Module "{obj.name}" updated.')
            return redirect("garages:settings", garage_slug=garage_slug)
        return render(request, self.template_name, {
            "garage": garage, "dm_form": dm_form, "object": obj, "is_new": False,
        })


class GarageDynamicModuleDeleteView(LoginRequiredMixin, GarageAdminMixin, View):
    template_name = "garages/settings/dynamic_module_confirm_delete.html"

    def get(self, request, garage_slug, pk):
        garage = self.get_garage()
        obj = get_object_or_404(DynamicModule, pk=pk, garage=garage)
        return render(request, self.template_name, {"garage": garage, "object": obj})

    def post(self, request, garage_slug, pk):
        garage = self.get_garage()
        obj = get_object_or_404(DynamicModule, pk=pk, garage=garage)
        name = obj.name
        obj.delete()
        messages.success(request, f'Module "{name}" deleted.')
        return redirect("garages:settings", garage_slug=garage_slug)


class GarageToggleDynamicModuleView(LoginRequiredMixin, GarageAdminMixin, View):
    def post(self, request, garage_slug, pk):
        garage = self.get_garage()
        obj = get_object_or_404(DynamicModule, pk=pk, garage=garage)
        obj.is_enabled = not obj.is_enabled
        obj.save(update_fields=["is_enabled"])
        state = "enabled" if obj.is_enabled else "disabled"
        messages.success(request, f'Module "{obj.name}" is now {state}.')
        return redirect("garages:settings", garage_slug=garage_slug)


class GarageDynamicModuleFieldsView(LoginRequiredMixin, GarageAdminMixin, View):
    template_name = "garages/settings/dynamic_module_fields.html"

    def get(self, request, garage_slug, pk):
        garage = self.get_garage()
        module = get_object_or_404(DynamicModule, pk=pk, garage=garage)
        return render(request, self.template_name, {
            "garage": garage, "module": module,
            "fields": module.fields.order_by("position", "label"),
        })


class GarageDynamicFieldCreateView(LoginRequiredMixin, GarageAdminMixin, View):
    template_name = "garages/settings/dynamic_field_form.html"

    def get(self, request, garage_slug, pk):
        garage = self.get_garage()
        module = get_object_or_404(DynamicModule, pk=pk, garage=garage)
        return render(request, self.template_name, {
            "garage": garage, "module": module,
            "field_form": GarageDynamicModuleFieldForm(), "is_new": True,
        })

    def post(self, request, garage_slug, pk):
        garage = self.get_garage()
        module = get_object_or_404(DynamicModule, pk=pk, garage=garage)
        field_form = GarageDynamicModuleFieldForm(request.POST)
        if field_form.is_valid():
            obj = field_form.save(commit=False)
            obj.module = module
            obj.save()
            messages.success(request, f'Field "{obj.label}" added.')
            return redirect("garages:dynamic_module_fields", garage_slug=garage_slug, pk=pk)
        return render(request, self.template_name, {
            "garage": garage, "module": module, "field_form": field_form, "is_new": True,
        })


class GarageDynamicFieldUpdateView(LoginRequiredMixin, GarageAdminMixin, View):
    template_name = "garages/settings/dynamic_field_form.html"

    def get(self, request, garage_slug, pk, field_pk):
        garage = self.get_garage()
        module = get_object_or_404(DynamicModule, pk=pk, garage=garage)
        field = get_object_or_404(DynamicModuleField, pk=field_pk, module=module)
        return render(request, self.template_name, {
            "garage": garage, "module": module,
            "field_form": GarageDynamicModuleFieldForm(instance=field),
            "object": field, "is_new": False,
        })

    def post(self, request, garage_slug, pk, field_pk):
        garage = self.get_garage()
        module = get_object_or_404(DynamicModule, pk=pk, garage=garage)
        field = get_object_or_404(DynamicModuleField, pk=field_pk, module=module)
        field_form = GarageDynamicModuleFieldForm(request.POST, instance=field)
        if field_form.is_valid():
            field_form.save()
            messages.success(request, f'Field "{field.label}" updated.')
            return redirect("garages:dynamic_module_fields", garage_slug=garage_slug, pk=pk)
        return render(request, self.template_name, {
            "garage": garage, "module": module,
            "field_form": field_form, "object": field, "is_new": False,
        })


class GarageDynamicFieldDeleteView(LoginRequiredMixin, GarageAdminMixin, View):
    template_name = "garages/settings/dynamic_field_confirm_delete.html"

    def get(self, request, garage_slug, pk, field_pk):
        garage = self.get_garage()
        module = get_object_or_404(DynamicModule, pk=pk, garage=garage)
        field = get_object_or_404(DynamicModuleField, pk=field_pk, module=module)
        return render(request, self.template_name, {"garage": garage, "module": module, "object": field})

    def post(self, request, garage_slug, pk, field_pk):
        garage = self.get_garage()
        module = get_object_or_404(DynamicModule, pk=pk, garage=garage)
        field = get_object_or_404(DynamicModuleField, pk=field_pk, module=module)
        label = field.label
        field.delete()
        messages.success(request, f'Field "{label}" deleted.')
        return redirect("garages:dynamic_module_fields", garage_slug=garage_slug, pk=pk)
