from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_alter_personeriasmlvprogresion_id"),
    ]

    operations = [
        migrations.CreateModel(
            name="VariableMacro",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("anio", models.IntegerField(verbose_name="Año")),
                ("tipo", models.CharField(
                    choices=[
                        ("SMLV", "Salario Mínimo Legal Vigente (SMLMV)"),
                        ("IPC", "Inflación (IPC)"),
                        ("PIB", "PIB Nacional ($ Corrientes)"),
                        ("PETROLEO", "Precio Barril Petróleo (US$)"),
                        ("DTF", "DTF (Tasa de interés)"),
                        ("TRM", "TRM (Tasa Cambio)"),
                    ],
                    max_length=10, verbose_name="Variable")),
                ("valor", models.DecimalField(decimal_places=4, default=0, max_digits=20, verbose_name="Valor")),
                ("pct_anual", models.DecimalField(decimal_places=4, default=0, max_digits=8,
                                                    help_text="Ej: 0.062 = 6.2%",
                                                    verbose_name="% Crecimiento Anual")),
                ("es_proyectado", models.BooleanField(default=False,
                                                        help_text="False = histórico real, True = proyección",
                                                        verbose_name="¿Es proyección?")),
            ],
            options={
                "verbose_name": "Variable Macro",
                "verbose_name_plural": "Variables Macro",
                "ordering": ["tipo", "anio"],
                "unique_together": {("anio", "tipo")},
            },
        ),
    ]
