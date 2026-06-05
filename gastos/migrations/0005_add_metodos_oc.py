from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gastos", "0004_rubrogasto_metodo_calculo"),
    ]

    operations = [
        migrations.AlterField(
            model_name="rubrogasto",
            name="metodo_calculo",
            field=models.CharField(
                choices=[
                    ("MAN", "Manual"),
                    ("DCAP", "Servicio Deuda - Capital (vigencia)"),
                    ("DINT", "Servicio Deuda - Intereses (vigencia)"),
                    ("DTOT", "Servicio Deuda - Total (Capital + Intereses + TCR)"),
                    ("PEN", "Costo total Pensionados (Fondo de Pensiones)"),
                    ("CPS", "Costo Personal por Sección (rubro = sección.cargo)"),
                    ("OCC", "Transferencia al Concejo (Anexo 6)"),
                    ("OCP", "Transferencia a la Personería (Anexo 6)"),
                ],
                default="MAN",
                max_length=4,
                verbose_name="Método de Cálculo",
            ),
        ),
    ]
