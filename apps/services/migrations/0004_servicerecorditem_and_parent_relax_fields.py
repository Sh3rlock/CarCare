from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0003_servicerecord_consumables"),
    ]

    operations = [
        migrations.AlterField(
            model_name="servicerecord",
            name="service_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("oil_change", "Oil Change"),
                    ("tire_rotation", "Tire Rotation"),
                    ("tire_replacement", "Tire Replacement"),
                    ("brake_service", "Brake Service"),
                    ("battery", "Battery"),
                    ("air_filter", "Air Filter"),
                    ("fuel_filter", "Fuel Filter"),
                    ("spark_plugs", "Spark Plugs"),
                    ("coolant", "Coolant Flush"),
                    ("transmission", "Transmission Service"),
                    ("inspection", "Inspection / MOT"),
                    ("repair", "Repair"),
                    ("other", "Other"),
                ],
                default="other",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="servicerecord",
            name="title",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.CreateModel(
            name="ServiceRecordItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "service_type",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("oil_change", "Oil Change"),
                            ("tire_rotation", "Tire Rotation"),
                            ("tire_replacement", "Tire Replacement"),
                            ("brake_service", "Brake Service"),
                            ("battery", "Battery"),
                            ("air_filter", "Air Filter"),
                            ("fuel_filter", "Fuel Filter"),
                            ("spark_plugs", "Spark Plugs"),
                            ("coolant", "Coolant Flush"),
                            ("transmission", "Transmission Service"),
                            ("inspection", "Inspection / MOT"),
                            ("repair", "Repair"),
                            ("other", "Other"),
                        ],
                        max_length=20,
                    ),
                ),
                ("replacement_part", models.CharField(blank=True, max_length=200)),
                ("part_price", models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ("consumable", models.CharField(blank=True, max_length=50)),
                ("note", models.TextField(blank=True)),
                ("work_hours", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "record",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="services.servicerecord",
                    ),
                ),
            ],
            options={"ordering": ["id"]},
        ),
    ]
