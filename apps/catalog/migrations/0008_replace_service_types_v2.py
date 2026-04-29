from django.db import migrations
from django.utils.text import slugify


SERVICE_TYPE_LABELS = [
    "Futómű",
    "Ablakpriccoló",
    "Lámpa",
    "Izzó",
    "Motor",
    "Fék",
    "Futószög",
    "Váltó",
    "Szervó",
    "Olaj csere",
    "Differenciálmű",
    "Légkondi",
    "Kipufogó",
    "Villamosság",
    "Vezérlés csere",
    "Ablaktörlő",
    "Kuplung",
    "Zárak",
]


def _unique_values(labels):
    counts = {}
    values = []
    for label in labels:
        base = slugify(label).replace("-", "_")[:44] or "service_type"
        idx = counts.get(base, 0) + 1
        counts[base] = idx
        value = base if idx == 1 else f"{base}_{idx}"
        values.append((value[:50], label))
    return values


def replace_service_types(apps, schema_editor):
    DropdownChoice = apps.get_model("catalog", "DropdownChoice")
    DropdownChoice.objects.filter(garage__isnull=True, list_key="service_type").delete()

    for position, (value, label) in enumerate(_unique_values(SERVICE_TYPE_LABELS)):
        DropdownChoice.objects.create(
            garage=None,
            list_key="service_type",
            value=value,
            label=label,
            position=position,
            is_active=True,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0007_replace_consumables"),
    ]

    operations = [
        migrations.RunPython(replace_service_types, migrations.RunPython.noop),
    ]

