"""Aplica el metodo OLEO (promedio 3 anos) al rubro de oleoductos.

Solo se aplica al rubro principal 1.1.01.02.214. El rubro de salud
(1.3.2.1.1.1.01.02.214) se deja como MAN porque su valor es un destination
de una porcion (no toda la base) y necesita un calculo distinto.

Si los 3 anios historicos en ParametrosSistema estan en 0, la formula OLEO
preserva el valor actual del rubro (ver utils.calcular_todos_ingresos),
asi que poner el metodo en OLEO antes de que el usuario llene los datos
historicos no rompe nada.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'presupuesto_project.settings')
django.setup()

from ingresos.models import RubroIngreso
from ingresos.utils import calcular_todos_ingresos
from core.models import ParametrosSistema


CODIGO_OLEO = '1.1.01.02.214'


def run():
    p = (ParametrosSistema.objects.filter(activo=True).first()
         or ParametrosSistema.objects.order_by('-vigencia').first())
    v = p.vigencia
    print(f'Vigencia: {v}')
    print(f'Historicos oleoductos: n-3={p.recaudo_oleoductos_anio_n3}, '
          f'n-2={p.recaudo_oleoductos_anio_n2}, n-1={p.recaudo_oleoductos_anio_n1}')

    cambios = 0
    for r in RubroIngreso.objects.filter(vigencia=v, codigo=CODIGO_OLEO, es_titulo=False):
        if r.metodo_calculo != 'OLEO':
            antes = r.metodo_calculo
            r.metodo_calculo = 'OLEO'
            r.save(update_fields=['metodo_calculo'])
            cambios += 1
            print(f'  {r.codigo} [{r.descripcion[:55]}]  {antes} -> OLEO  valor={r.valor_apropiacion:,.0f}')
        else:
            print(f'  {r.codigo} ya estaba en OLEO')

    print(f'\n{cambios} rubro(s) actualizado(s).')
    print('\n== Recalculando ==')
    calcular_todos_ingresos(v)
    for r in RubroIngreso.objects.filter(vigencia=v, codigo=CODIGO_OLEO, es_titulo=False):
        print(f'  {r.codigo} valor final = {r.valor_apropiacion:,.0f}')


if __name__ == '__main__':
    run()
