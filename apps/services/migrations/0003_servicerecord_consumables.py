from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0002_servicerecord_custom_data"),
    ]

    operations = [
        migrations.AddField(
            model_name="servicerecord",
            name="consumables",
            field=models.CharField(blank=True, max_length=50),
        ),
    ]
