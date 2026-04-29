from django.db import migrations


SERVICE_TYPES = [
    ("oil_change", "Oil Change", 0),
    ("tire_rotation", "Tire Rotation", 1),
    ("tire_replacement", "Tire Replacement", 2),
    ("brake_service", "Brake Service", 3),
    ("battery", "Battery", 4),
    ("air_filter", "Air Filter", 5),
    ("fuel_filter", "Fuel Filter", 6),
    ("spark_plugs", "Spark Plugs", 7),
    ("coolant", "Coolant Flush", 8),
    ("transmission", "Transmission Service", 9),
    ("inspection", "Inspection / MOT", 10),
    ("repair", "Repair", 11),
    ("other", "Other", 12),
]


def seed_service_types(apps, schema_editor):
    DropdownChoice = apps.get_model("catalog", "DropdownChoice")
    for value, label, position in SERVICE_TYPES:
        DropdownChoice.objects.get_or_create(
            garage=None,
            list_key="service_type",
            value=value,
            defaults={"label": label, "position": position, "is_active": True},
        )


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0004_alter_dropdownchoice_list_key"),
    ]

    operations = [
        migrations.RunPython(seed_service_types, migrations.RunPython.noop),
    ]
