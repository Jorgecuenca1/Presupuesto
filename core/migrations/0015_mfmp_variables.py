from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_techoinversion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='variablemacro',
            name='tipo',
            field=models.CharField(
                choices=[
                    ('SMLV', 'Salario Mínimo Legal Vigente (SMLMV)'),
                    ('IPC', 'Inflación (IPC) fin de periodo (%)'),
                    ('PIB', 'PIB Nacional ($ Corrientes)'),
                    ('PETROLEO', 'Precio Barril Petróleo Brent (USD)'),
                    ('DTF', 'DTF (Tasa de interés)'),
                    ('TRM', 'TRM promedio (USD/COP)'),
                    ('PIB_R', 'Crecimiento del PIB real (%)'),
                    ('PIB_N', 'Crecimiento del PIB nominal (%)'),
                    ('SOCIOS', 'Crecimiento socios comerciales (%)'),
                    ('CTA_CORR', 'Balance de cuenta corriente (% PIB)'),
                    ('DEPREC', 'Depreciación tasa de cambio (%)'),
                    ('PROD_PET', 'Producción de petróleo (KBPD)'),
                    ('ING_GNC', 'Ingresos totales del GNC (% PIB)'),
                    ('GTO_GNC', 'Gastos totales del GNC (% PIB)'),
                    ('BAL_GNC', 'Balance fiscal del GNC (% PIB)'),
                    ('BAL_PRIM', 'Balance primario del GNC (% PIB)'),
                    ('T_LOCAL', 'Tasa de interés local (%, promedio)'),
                    ('T_EXT', 'Tasa de interés externa (%, promedio)'),
                    ('D_NETA', 'Deuda neta del GNC (% PIB)'),
                    ('BAL_GG', 'Balance fiscal del GG (% PIB)'),
                    ('D_GG', 'Deuda consolidada del GG (% PIB)'),
                ],
                max_length=10, verbose_name='Variable',
            ),
        ),
    ]
