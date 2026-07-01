from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gastos', '0008_costopersonal_extras'),
    ]

    operations = [
        migrations.AddField(
            model_name='contratocredito',
            name='fecha_firma',
            field=models.DateField(blank=True, null=True, verbose_name='Fecha Firma Contrato'),
        ),
        migrations.AddField(
            model_name='contratocredito',
            name='tasa_ea',
            field=models.DecimalField(decimal_places=6, default=0, help_text='Efectiva anual, ej: 0.1355 = 13.55%', max_digits=8, verbose_name='Tasa Interés E.A.'),
        ),
        migrations.AddField(
            model_name='contratocredito',
            name='tcr_default',
            field=models.DecimalField(decimal_places=6, default=0, help_text='Tasa Cobertura Riesgo default para nuevos pagarés', max_digits=8, verbose_name='TCR default'),
        ),
        migrations.AddField(
            model_name='contratocredito',
            name='gracia_meses',
            field=models.IntegerField(default=0, verbose_name='Gracia Capital (meses)'),
        ),
        migrations.AddField(
            model_name='contratocredito',
            name='num_cuotas_capital',
            field=models.IntegerField(default=0, verbose_name='Nº Cuotas Capital'),
        ),
    ]
