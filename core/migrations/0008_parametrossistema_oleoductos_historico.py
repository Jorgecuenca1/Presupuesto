from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0007_parametrossistema_pct_pagos_despacho_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="parametrossistema",
            name="recaudo_oleoductos_anio_n3",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Recaudo histórico hace 3 años (vigencia - 3)",
                max_digits=20,
                verbose_name="Recaudo Oleoductos hace 3 años ($)",
            ),
        ),
        migrations.AddField(
            model_name="parametrossistema",
            name="recaudo_oleoductos_anio_n2",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Recaudo histórico hace 2 años (vigencia - 2)",
                max_digits=20,
                verbose_name="Recaudo Oleoductos hace 2 años ($)",
            ),
        ),
        migrations.AddField(
            model_name="parametrossistema",
            name="recaudo_oleoductos_anio_n1",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Recaudo histórico del año anterior (vigencia - 1)",
                max_digits=20,
                verbose_name="Recaudo Oleoductos año anterior ($)",
            ),
        ),
    ]
