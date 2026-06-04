"""Fix metodo_calculo de los 4 rubros hoja del Impuesto Predial.

Sin esto los rubros quedan como MAN (manual) con valores fijos, y el reporte del
Anexo 1 no refleja lo que calcula realmente el motor de predial (ResumenCalculo
+ calcular_predial_vigencias_anteriores). El usuario reportaba que el reporte
parecia un mockup: este script reclasifica los rubros y ejecuta el recalculo.

Idempotente. Conserva todos los datos. No toca contribuyentes, tarifas ni cartera.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'presupuesto_project.settings')
django.setup()

from ingresos.models import RubroIngreso
from ingresos.utils import calcular_todos_ingresos
from core.models import ParametrosSistema


MAPEO = {
    '1.1.01.01.200.01.01': 'PUVA',
    '1.1.01.01.200.01.02': 'PUAN',
    '1.1.01.01.200.02.01': 'PRVA',
    '1.1.01.01.200.02.02': 'PRAN',
}


def run():
    p = (ParametrosSistema.objects.filter(activo=True).first()
         or ParametrosSistema.objects.order_by('-vigencia').first())
    if not p:
        print('No hay ParametrosSistema; abortando.')
        return
    v = p.vigencia
    print(f'Vigencia activa: {v}')

    print('\n== Estado ANTES ==')
    for cod in MAPEO:
        r = RubroIngreso.objects.filter(vigencia=v, codigo=cod).first()
        if r:
            print(f'  {cod} [{r.metodo_calculo}] {r.descripcion[:48]:48} = {r.valor_apropiacion:,.0f}')
        else:
            print(f'  {cod} NO ENCONTRADO')

    print('\n== Reclasificando ==')
    cambios = 0
    for cod, metodo in MAPEO.items():
        r = RubroIngreso.objects.filter(vigencia=v, codigo=cod).first()
        if r and r.metodo_calculo != metodo:
            r.metodo_calculo = metodo
            r.save(update_fields=['metodo_calculo'])
            cambios += 1
            print(f'  {cod}: MAN -> {metodo}')
    print(f'{cambios} rubros reclasificados.')

    print('\n== Ejecutando calcular_todos_ingresos ==')
    calcular_todos_ingresos(v)

    print('\n== Estado DESPUES ==')
    for cod in MAPEO:
        r = RubroIngreso.objects.filter(vigencia=v, codigo=cod).first()
        if r:
            print(f'  {cod} [{r.metodo_calculo}] {r.descripcion[:48]:48} = {r.valor_apropiacion:,.0f}')

    print('\n== Titulos padres ==')
    for cod in ['1.1.01.01.200', '1.1.01.01.200.01', '1.1.01.01.200.02']:
        r = RubroIngreso.objects.filter(vigencia=v, codigo=cod).first()
        if r:
            print(f'  {cod} {r.descripcion[:60]:60} = {r.valor_apropiacion:,.0f}')


if __name__ == '__main__':
    run()
