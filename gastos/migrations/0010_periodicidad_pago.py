from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gastos', '0009_contrato_supuestos'),
    ]

    operations = [
        migrations.AddField(
            model_name='contratocredito',
            name='periodicidad_pago',
            field=models.CharField(
                choices=[('M', 'Mensual'), ('T', 'Trimestral'), ('S', 'Semestral'), ('A', 'Anual')],
                default='T', max_length=1, verbose_name='Periodicidad de Pago',
            ),
        ),
    ]
