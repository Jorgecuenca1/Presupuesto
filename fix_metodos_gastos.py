"""Ajusta los metodos de calculo de los rubros de gasto:

1. Quita OCC/OCP de los rubros huerfanos `01.2` y `02.2` (sin FK seccion):
   el tope Anexo 6 se muestra en el reporte como referencia, no como un
   monto inflado en la jerarquia. Volvemos a MAN con valor 0.

2. Asigna DCAP al rubro de Banca Comercial CAPITAL:
   `2.2.2.01.02.002.02.03-02 Banca comercial` (capital prestamos).
   Cuando se carguen amortizaciones para la vigencia se actualizara.

3. Asigna DINT al rubro de Banca Comercial INTERESES:
   `2.2.2.02.02.002.02.03-02 Banca comercial` (intereses prestamos).

Idempotente. No borra datos.
"""
import os
from decimal import Decimal
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'presupuesto_project.settings')
django.setup()

from gastos.models import RubroGasto
from gastos.utils import recalcular_rubros_metodo
from core.models import ParametrosSistema


REVERTIR_A_MAN = ['01.2', '02.2']  # wrappers huerfanos
DCAP_CODIGOS = ['2.2.2.01.02.002.02.03-02']
DINT_CODIGOS = ['2.2.2.02.02.002.02.03-02']


def run():
    p = (ParametrosSistema.objects.filter(activo=True).first()
         or ParametrosSistema.objects.order_by('-vigencia').first())
    v = p.vigencia
    print(f'Vigencia: {v}')

    print('\n== Revirtiendo wrappers 01.2 y 02.2 a MAN (sin seccion) ==')
    for cod in REVERTIR_A_MAN:
        for r in RubroGasto.objects.filter(vigencia=v, codigo=cod, seccion__isnull=True):
            if r.metodo_calculo != 'MAN':
                ant = r.metodo_calculo
                r.metodo_calculo = 'MAN'
                r.valor_apropiacion = Decimal('0')
                r.save(update_fields=['metodo_calculo', 'valor_apropiacion'])
                print(f'  {cod}: {ant} -> MAN, valor=0')

    print('\n== Asignando DCAP a Banca Comercial (Capital) ==')
    for cod in DCAP_CODIGOS:
        for r in RubroGasto.objects.filter(vigencia=v, codigo=cod, es_titulo=False):
            if r.metodo_calculo != 'DCAP':
                ant = r.metodo_calculo
                r.metodo_calculo = 'DCAP'
                r.save(update_fields=['metodo_calculo'])
                print(f'  {cod}: {ant} -> DCAP  [sec={r.seccion_id}]  desc={r.descripcion[:55]}')

    print('\n== Asignando DINT a Banca Comercial (Intereses) ==')
    for cod in DINT_CODIGOS:
        for r in RubroGasto.objects.filter(vigencia=v, codigo=cod, es_titulo=False):
            if r.metodo_calculo != 'DINT':
                ant = r.metodo_calculo
                r.metodo_calculo = 'DINT'
                r.save(update_fields=['metodo_calculo'])
                print(f'  {cod}: {ant} -> DINT  [sec={r.seccion_id}]  desc={r.descripcion[:55]}')

    print('\n== Recalculando ==')
    resumen = recalcular_rubros_metodo(v)
    for m, info in resumen.items():
        if info['rubros']:
            print(f'  {m}: {info["rubros"]} rubros, ${info["total_aplicado"]:,.0f}')

    print('\nNota: DCAP/DINT mostraran 0 hasta que se carguen las AmortizacionPagare '
          'para la vigencia (Pagares > Amortizaciones).')


if __name__ == '__main__':
    run()
