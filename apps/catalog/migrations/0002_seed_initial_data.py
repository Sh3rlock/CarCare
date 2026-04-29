from django.db import migrations

MAKES = [
    "Abarth", "Alfa Romeo", "Aston Martin", "Audi", "Bentley", "BMW",
    "Bugatti", "Buick", "Cadillac", "Chevrolet", "Chrysler", "Citroën",
    "Dacia", "Dodge", "DS Automobiles", "Ferrari", "Fiat", "Ford",
    "Genesis", "Honda", "Hyundai", "Infiniti", "Jaguar", "Jeep",
    "Kia", "Lamborghini", "Land Rover", "Lexus", "Lincoln", "Maserati",
    "Mazda", "McLaren", "Mercedes-Benz", "MINI", "Mitsubishi", "Nissan",
    "Opel", "Peugeot", "Porsche", "RAM", "Renault", "Rolls-Royce",
    "SEAT", "Škoda", "Smart", "Subaru", "Suzuki", "Tesla", "Toyota",
    "Vauxhall", "Volkswagen", "Volvo",
]

FUEL_TYPES = [
    ("petrol",   "Petrol",   0),
    ("diesel",   "Diesel",   1),
    ("electric", "Electric", 2),
    ("hybrid",   "Hybrid",   3),
    ("lpg",      "LPG",      4),
    ("other",    "Other",    5),
]

TRANSMISSIONS = [
    ("manual",    "Manual",         0),
    ("automatic", "Automatic",      1),
    ("semi_auto", "Semi-Automatic", 2),
]


def seed_data(apps, schema_editor):
    CarMake = apps.get_model("catalog", "CarMake")
    DropdownChoice = apps.get_model("catalog", "DropdownChoice")

    for i, name in enumerate(MAKES):
        CarMake.objects.get_or_create(name=name, defaults={"position": i, "is_active": True})

    for value, label, pos in FUEL_TYPES:
        DropdownChoice.objects.get_or_create(
            list_key="fuel_type", value=value,
            defaults={"label": label, "position": pos, "is_active": True},
        )

    for value, label, pos in TRANSMISSIONS:
        DropdownChoice.objects.get_or_create(
            list_key="transmission", value=value,
            defaults={"label": label, "position": pos, "is_active": True},
        )


def unseed_data(apps, schema_editor):
    pass  # leave data in place on rollback


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_data, unseed_data),
    ]
