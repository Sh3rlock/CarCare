from django.db.models import Q

from .models import CarMake, CarModel, DropdownChoice


def get_active_makes(garage=None):
    """Return sorted make names visible to a garage: global + garage-specific."""
    q = Q(garage__isnull=True)
    if garage is not None:
        q |= Q(garage=garage)
    names = (
        CarMake.objects.filter(q, is_active=True)
        .values_list("name", flat=True)
        .distinct()
    )
    return sorted(names)


def get_active_models(make_name, garage=None):
    """Return sorted model names for a make name: global + garage-specific."""
    q = Q(garage__isnull=True)
    if garage is not None:
        q |= Q(garage=garage)
    names = (
        CarModel.objects.filter(q, make__name=make_name, is_active=True)
        .values_list("name", flat=True)
        .distinct()
    )
    return sorted(names)


def get_dropdown_choices(list_key, garage=None):
    """Return (value, label) pairs for a dropdown list, merging global + garage overrides."""
    global_items = list(
        DropdownChoice.objects.filter(list_key=list_key, is_active=True, garage__isnull=True)
        .order_by("position", "label")
        .values_list("value", "label")
    )
    if garage is None:
        return global_items

    garage_overrides = {
        d.value: d.label
        for d in DropdownChoice.objects.filter(list_key=list_key, is_active=True, garage=garage)
    }
    merged = [(v, garage_overrides.get(v, l)) for v, l in global_items]
    seen = {v for v, _ in global_items}
    for value, label in garage_overrides.items():
        if value not in seen:
            merged.append((value, label))
    return merged
