from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gastos", "0007_costopersonal_salario_anterior"),
    ]

    operations = [
        migrations.AddField(
            model_name="costopersonal",
            name="bonif_servicios_prestados",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14,
                verbose_name="Bonif. Servicios Prestados ($)"),
        ),
        migrations.AddField(
            model_name="costopersonal",
            name="bonif_recreacion",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14,
                verbose_name="Bonif. Recreación ($)"),
        ),
        migrations.AddField(
            model_name="costopersonal",
            name="aportes_esap",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14,
                verbose_name="Aporte ESAP ($)"),
        ),
        migrations.AddField(
            model_name="costopersonal",
            name="aportes_escuelas",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14,
                verbose_name="Aporte Escuelas Industriales ($)"),
        ),
        migrations.AddField(
            model_name="costopersonal",
            name="bonif_direccion",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14,
                verbose_name="Bonif. Dirección ($)"),
        ),
        migrations.AddField(
            model_name="costopersonal",
            name="bonif_territorial",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14,
                verbose_name="Bonif. Territorial ($)"),
        ),
        migrations.AddField(
            model_name="costopersonal",
            name="subsidio_transporte_anual",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14,
                verbose_name="Subsidio Transporte Anual ($)"),
        ),
    ]
