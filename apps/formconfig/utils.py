from .models import BuiltinFieldConfig, CustomField, DynamicModule, ModuleConfig

MODULE_LABELS = {
    "services": "Service Records",
    "quotes": "Quotes",
    "parts": "Part Replacements",
    "mileage": "Mileage Log",
    "insurance": "Insurance Policy",
    "documents": "Documents & Images",
    "reminders": "Reminders",
}

FORM_FIELD_DEFINITIONS = {
    "vehicle": [
        ("client", "Client"),
        ("make", "Make"),
        ("model", "Model"),
        ("year", "Year"),
        ("license_plate", "License Plate"),
        ("fuel_type", "Fuel Type"),
        ("transmission", "Transmission"),
        ("color", "Color"),
        ("ccm", "Engine (ccm)"),
        ("hp", "Horsepower (HP)"),
        ("engine_code", "Engine Code"),
        ("doors", "Doors"),
        ("has_ac", "Air Conditioning"),
        ("drive_type", "Drive Type"),
        ("vin", "VIN"),
        ("notes", "Notes"),
    ],
    "client": [
        ("first_name", "First Name"),
        ("last_name", "Last Name"),
        ("company", "Company / Organisation"),
        ("email", "Email"),
        ("phone", "Phone"),
        ("address", "Address"),
        ("notes", "Notes"),
    ],
    "service": [
        ("date", "Dátum"),
        ("mileage", "Kilométeróra állás"),
        ("cost", "Teljes költség"),
        ("notes", "Megjegyzés"),
        ("item_service_type", "Sor: Szerviztípus"),
        ("item_replacement_part", "Sor: Cserélt alkatrész"),
        ("item_part_price", "Sor: Alkatrész ára"),
        ("item_consumable", "Sor: Fogyóanyag"),
        ("item_note", "Sor: Megjegyzés"),
        ("item_work_hours", "Sor: Munkaóra"),
    ],
    "quote": [
        ("date", "Dátum"),
        ("title", "Cím"),
        ("total_estimate", "Becsült végösszeg"),
        ("notes", "Megjegyzés"),
        ("item_service_type", "Sor: Szerviztípus"),
        ("item_replacement_part", "Sor: Cserélt alkatrész"),
        ("item_part_price", "Sor: Alkatrész ára"),
        ("item_consumable", "Sor: Fogyóanyag"),
        ("item_note", "Sor: Megjegyzés"),
        ("item_work_hours", "Sor: Munkaóra"),
    ],
    "part": [
        ("part_type", "Part Type"),
        ("part_name", "Part Name"),
        ("part_number", "Part Number"),
        ("brand", "Brand"),
        ("date", "Date"),
        ("mileage_at_replacement", "Mileage at Replacement"),
        ("next_replacement_mileage", "Next Replacement Mileage"),
        ("next_replacement_date", "Next Replacement Date"),
        ("cost", "Cost"),
        ("workshop", "Workshop / Mechanic"),
        ("notes", "Notes"),
    ],
    "mileage": [
        ("date", "Date"),
        ("odometer", "Odometer"),
        ("notes", "Notes"),
    ],
    "insurance": [
        ("provider", "Insurance Provider"),
        ("policy_number", "Policy Number"),
        ("coverage_type", "Coverage Type"),
        ("start_date", "Start Date"),
        ("end_date", "End Date"),
        ("premium", "Premium"),
        ("premium_period", "Premium Period"),
        ("agent_name", "Agent Name"),
        ("agent_phone", "Agent Phone"),
        ("notes", "Notes"),
    ],
    "reminder": [
        ("title", "Reminder Title"),
        ("due_date", "Due Date"),
        ("due_mileage", "Due Mileage"),
        ("notes", "Notes"),
    ],
}

# Fields that cannot be hidden — model requires them (non-blank, non-null)
PROTECTED_FIELDS = {
    "vehicle": {"make", "model", "year", "license_plate"},
    "client": {"first_name"},
    "service": {"date"},
    "quote": {"date"},
    "part": {"part_name", "date"},
    "mileage": {"date", "odometer"},
    "insurance": {"provider", "policy_number", "start_date", "end_date"},
    "reminder": {"title"},
}

FORM_LABELS = {
    "vehicle": "Vehicle",
    "client": "Client",
    "service": "Service Record",
    "quote": "Quote",
    "part": "Part Replacement",
    "mileage": "Mileage Log",
    "insurance": "Insurance Policy",
    "reminder": "Reminder",
}


def get_enabled_modules(garage=None):
    """Return the set of enabled module keys.

    When garage is given, garage-specific settings override the global defaults.
    """
    global_disabled = set(
        ModuleConfig.objects.filter(
            garage__isnull=True, is_enabled=False
        ).values_list("module_key", flat=True)
    )
    if garage is None:
        return {key for key in MODULE_LABELS if key not in global_disabled}

    garage_overrides = dict(
        ModuleConfig.objects.filter(garage=garage).values_list("module_key", "is_enabled")
    )
    result = set()
    for key in MODULE_LABELS:
        if key in garage_overrides:
            if garage_overrides[key]:
                result.add(key)
        elif key not in global_disabled:
            result.add(key)
    return result


def get_hidden_fields(form_key, garage=None):
    """Return the set of hidden field names, garage overrides global."""
    global_visibility = {
        c.field_name: c.is_visible
        for c in BuiltinFieldConfig.objects.filter(
            garage__isnull=True, form_key=form_key
        )
    }
    if garage is not None:
        for c in BuiltinFieldConfig.objects.filter(garage=garage, form_key=form_key):
            global_visibility[c.field_name] = c.is_visible  # garage wins
    return {name for name, visible in global_visibility.items() if not visible}


def get_label_overrides(form_key, garage=None):
    """Return {field_name: label_override}, garage overrides global."""
    overrides = {
        c.field_name: c.label_override
        for c in BuiltinFieldConfig.objects.filter(
            garage__isnull=True, form_key=form_key
        ).exclude(label_override="")
    }
    if garage is not None:
        for c in BuiltinFieldConfig.objects.filter(
            garage=garage, form_key=form_key
        ).exclude(label_override=""):
            overrides[c.field_name] = c.label_override  # garage wins
    return overrides


def get_custom_fields(form_key, garage=None):
    """Return custom fields; when garage given, garage fields supplement globals
    (same field_key → garage version wins).
    """
    qs = CustomField.objects.filter(form_key=form_key, is_visible=True)
    if garage is None:
        return qs.filter(garage__isnull=True).order_by("position", "label")
    global_fields = {c.field_key: c for c in qs.filter(garage__isnull=True)}
    garage_fields = {c.field_key: c for c in qs.filter(garage=garage)}
    merged = {**global_fields, **garage_fields}
    return sorted(merged.values(), key=lambda c: (c.position, c.label))


def get_enabled_dynamic_modules(garage=None):
    """Return enabled DynamicModules for the given scope (global or garage)."""
    qs = DynamicModule.objects.filter(is_enabled=True)
    if garage is None:
        return qs.filter(garage__isnull=True).order_by("position", "name")
    return qs.filter(garage=garage).order_by("position", "name")
