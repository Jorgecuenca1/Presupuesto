from decimal import Decimal
from django.db import migrations, models


def actualizar_defaults(apps, schema_editor):
    """Actualiza defaults de campos existentes a los valores sector publico."""
    PS = apps.get_model('core', 'ParametrosSistema')
    for p in PS.objects.all():
        cambios = False
        # Prima de servicios sector publico: 15 dias = 4.17% (Dto 1042/78 art. 58)
        if p.pct_prima_servicios == Decimal('0.0833'):
            p.pct_prima_servicios = Decimal('0.0417')
            cambios = True
        if cambios:
            p.save()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0012_parametros_gastos"),
    ]

    operations = [
        migrations.AddField(
            model_name="parametrossistema",
            name="pct_bonif_servicios_prestados_alto",
            field=models.DecimalField(
                decimal_places=4, default=Decimal('0.35'), max_digits=6,
                verbose_name='% BSP Sueldo Alto (> umbral)',
                help_text='Decreto 1042/1978 art. 45 + Dto 330/2018. Default 35% para sueldos > 2 SMLMV',
            ),
        ),
        migrations.AddField(
            model_name="parametrossistema",
            name="umbral_smlmv_bsp",
            field=models.DecimalField(
                decimal_places=2, default=Decimal('2.00'), max_digits=4,
                verbose_name='Umbral SMLMV para BSP',
                help_text='Si salario_mensual ≤ umbral × SMLMV → BSP bajo (50%); sino BSP alto (35%). Dto 1042/78 + Dto 330/2018.',
            ),
        ),
        migrations.AlterField(
            model_name="parametrossistema",
            name="pct_bonif_servicios_prestados",
            field=models.DecimalField(
                decimal_places=4, default=Decimal('0.50'), max_digits=6,
                verbose_name='% BSP Sueldo Bajo (≤ umbral)',
                help_text='Decreto 1042/1978 art. 45 + Dto 330/2018. Default 50% para sueldos ≤ 2 SMLMV',
            ),
        ),
        migrations.AlterField(
            model_name="parametrossistema",
            name="pct_prima_servicios",
            field=models.DecimalField(
                decimal_places=4, default=Decimal('0.0417'), max_digits=6,
                verbose_name='% Prima de Servicios',
                help_text='Sector público: 15 días = 4.17% (Dto 1042/78 art. 58). Sector privado: 8.33% = 1 mes.',
            ),
        ),
        migrations.RunPython(actualizar_defaults, migrations.RunPython.noop),
    ]
