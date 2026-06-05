from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_anexo6_organos_control"),
    ]

    operations = [
        migrations.AlterField(
            model_name="personeriasmlvprogresion",
            name="id",
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
        ),
    ]
