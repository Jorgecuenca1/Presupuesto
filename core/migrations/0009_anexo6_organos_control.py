from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_parametrossistema_oleoductos_historico"),
    ]

    operations = [
        migrations.AddField(
            model_name="parametrossistema",
            name="icld_calculado",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Ingresos Corrientes de Libre Destinación del año anterior. "
                          "Se autollena desde Cifras Históricas si está en 0; editable.",
                max_digits=20,
                verbose_name="ICLD vigencia anterior ($)",
            ),
        ),
        migrations.AddField(
            model_name="parametrossistema",
            name="pct_icld_adicional_concejo",
            field=models.DecimalField(
                decimal_places=4,
                default=Decimal("0.015"),
                help_text="% sobre ICLD para sumar al Vr Honorarios del Concejo. Ej: 0.015 = 1.5% (Excel Anexo 6).",
                max_digits=6,
                verbose_name="% ICLD Adicional Concejo",
            ),
        ),
        migrations.AddField(
            model_name="tablaconcejopersoneria",
            name="valor_sesion_concejal",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Honorario por sesión (Ej. cat 5: $348.256)",
                max_digits=12,
                verbose_name="Valor Sesión Concejal ($)",
            ),
        ),
        migrations.AddField(
            model_name="tablaconcejopersoneria",
            name="personeria_smlv_fijo",
            field=models.IntegerField(
                default=0,
                help_text="Para categorías con SMLV fijo (3ª=400, 4ª=330, 6ª=0). "
                          "La 5ª usa la tabla PersoneriaSMLVProgresion por vigencia.",
                verbose_name="Personería SMLV Fijo",
            ),
        ),
        migrations.AlterField(
            model_name="tablaconcejopersoneria",
            name="honorario_concejal_smlmv",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Legado. Solo si valor_sesion_concejal=0",
                max_digits=6,
                verbose_name="Honorario Concejal (factor SMLMV)",
            ),
        ),
        migrations.AlterField(
            model_name="tablaconcejopersoneria",
            name="limite_concejo_pct_icld",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Tope legal Ley 617. Solo referencia.",
                max_digits=6,
                verbose_name="Límite Concejo (% ICLD)",
            ),
        ),
        migrations.AlterField(
            model_name="tablaconcejopersoneria",
            name="limite_personeria_pct_icld",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Para Especial/1ª/2ª (cálculo por % ICLD)",
                max_digits=6,
                verbose_name="Límite Personería (% ICLD)",
            ),
        ),
        migrations.CreateModel(
            name="PersoneriaSMLVProgresion",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("vigencia", models.IntegerField(verbose_name="Vigencia Fiscal")),
                ("categoria", models.IntegerField(
                    choices=[(0, "Especial"), (1, "Primera"), (2, "Segunda"),
                             (3, "Tercera"), (4, "Cuarta"), (5, "Quinta"), (6, "Sexta")],
                    verbose_name="Categoría Municipio")),
                ("smlv", models.IntegerField(
                    help_text="Número de salarios mínimos legales vigentes (Ej: 220)",
                    verbose_name="SMLV")),
            ],
            options={
                "verbose_name": "Progresión SMLV Personería",
                "verbose_name_plural": "Progresiones SMLV Personería",
                "ordering": ["categoria", "vigencia"],
                "unique_together": {("vigencia", "categoria")},
            },
        ),
    ]
