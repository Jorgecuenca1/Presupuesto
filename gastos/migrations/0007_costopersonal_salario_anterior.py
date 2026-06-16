from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gastos", "0006_costopersonal_total_override"),
    ]

    operations = [
        migrations.AddField(
            model_name="costopersonal",
            name="salario_basico_anterior",
            field=models.DecimalField(
                decimal_places=2, default=Decimal('0'), max_digits=14,
                help_text="Salario básico mensual del año anterior. Usado para calcular % incremento.",
                verbose_name="Salario Básico Mensual Año Anterior ($)",
            ),
        ),
        migrations.AddField(
            model_name="costopersonal",
            name="pct_incremento",
            field=models.DecimalField(
                decimal_places=4, default=Decimal('0'), max_digits=6,
                help_text="% incremento sobre año anterior. Si está vacío usa pct_incremento_salarial de Parámetros.",
                verbose_name="% Incremento sobre año anterior",
            ),
        ),
    ]
