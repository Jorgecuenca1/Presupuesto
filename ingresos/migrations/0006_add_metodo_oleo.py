from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ingresos", "0005_estampilla_codigo_rubro_pensiones_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="rubroingreso",
            name="metodo_calculo",
            field=models.CharField(
                choices=[
                    ("PUVA", "Cálculo Predial Urbano Vig. Actual"),
                    ("PUAN", "Cálculo Predial Urbano Vig. Anteriores"),
                    ("PRVA", "Cálculo Predial Rural Vig. Actual"),
                    ("PRAN", "Cálculo Predial Rural Vig. Anteriores"),
                    ("ICAI", "Cálculo ICA Industrial"),
                    ("ICAC", "Cálculo ICA Comercial"),
                    ("ICAS", "Cálculo ICA Servicios"),
                    ("AT", "15% del Total ICA"),
                    ("IPC", "Incremento IPC sobre Recaudo Anterior"),
                    ("ICN", "Tasa Crecimiento ICN sobre Recaudo Anterior"),
                    ("POAI", "Tarifa % sobre POAI Inversión"),
                    ("EST", "Cálculo Estampilla (Base × Tarifa)"),
                    ("OLEO", "Promedio últimos 3 años (Oleoductos)"),
                    ("MAN", "Valor Manual"),
                ],
                default="MAN",
                max_length=4,
            ),
        ),
    ]
