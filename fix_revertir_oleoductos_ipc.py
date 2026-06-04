"""Revierte a MAN los rubros de oleoductos/gasoductos incluidos por error como IPC.

Segun el seeder original (crear_datos_iniciales.py) y la indicacion del usuario,
el Impuesto de Transporte por Oleoductos NO se proyecta con IPC sino con
promedio geometrico (calculo aparte). Por consistencia se vuelve a MAN y se
preserva el valor actual (no se toca valor_apropiacion).

recaudo_vigencia_anterior se deja como esta (no afecta a MAN), por trazabilidad.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'presupuesto_project.settings')
django.setup()

from ingresos.models import RubroIngreso
from ingresos.utils import calcular_todos_ingresos
from core.models import ParametrosSistema


CODIGOS_NO_IPC = [
    '1.1.01.02.214',          # Impuesto de transporte por oleoductos y gasoductos
    '1.3.2.1.1.1.01.02.214',  # idem (salud)
]


def run():
    p = (ParametrosSistema.objects.filter(activo=True).first()
         or ParametrosSistema.objects.order_by('-vigencia').first())
    v = p.vigencia
    print(f'Vigencia: {v}')

    print('\n== Revirtiendo de IPC a MAN ==')
    for cod in CODIGOS_NO_IPC:
        for r in RubroIngreso.objects.filter(vigencia=v, codigo=cod, es_titulo=False):
            if r.metodo_calculo == 'IPC':
                r.metodo_calculo = 'MAN'
                r.save(update_fields=['metodo_calculo'])
                print(f'  {cod} [{r.descripcion[:55]}]  -> MAN  valor={r.valor_apropiacion:,.0f}')
            else:
                print(f'  {cod} ya en {r.metodo_calculo}, no se toca.')

    print('\n== Recalculando ==')
    calcular_todos_ingresos(v)
    print('Listo.')


if __name__ == '__main__':
    run()
