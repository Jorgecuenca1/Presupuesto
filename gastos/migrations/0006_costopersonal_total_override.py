from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gastos", "0005_add_metodos_oc"),
    ]

    operations = [
        migrations.AddField(
            model_name="costopersonal",
            name="costo_total_anual_override",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Si > 0 sobreescribe el costo total anual calculado desde los componentes. "
                          "Útil para importar el Gran Total directo del Excel sin desglosarlo en cada concepto.",
                max_digits=20,
                verbose_name="Costo Total Anual Override ($)",
            ),
        ),
    ]
