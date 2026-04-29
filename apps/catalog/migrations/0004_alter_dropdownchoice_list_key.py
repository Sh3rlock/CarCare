from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0003_garage_per_catalog"),
    ]

    operations = [
        migrations.AlterField(
            model_name="dropdownchoice",
            name="list_key",
            field=models.CharField(
                choices=[
                    ("fuel_type", "Fuel Type"),
                    ("transmission", "Transmission"),
                    ("service_type", "Service Type"),
                    ("consumables", "Consumables"),
                ],
                max_length=50,
            ),
        ),
    ]
