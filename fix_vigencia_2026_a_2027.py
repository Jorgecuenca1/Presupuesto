"""Mueve toda la data de vigencia=2026 a vigencia=2027.

Por indicacion del usuario: "estamos calculando 2027". Lo que estaba
etiquetado como 2026 ahora es el presupuesto en preparacion para 2027.

Tambien agrega la progresion SMLV Personeria para categoria 6
(Ley 2461/2025: 2025=200, 2026=210, 2027=220, 2028=230, 2029=240) y
asegura cat 5 con sus 5 anos cargados.

NO renombra:
- PersoneriaSMLVProgresion.vigencia (representa el ano legal especifico,
  cada fila es por ano y no se mueve)
- CifraHistoricaIngreso.anio / CifraHistoricaGasto.anio (anio historico real)
- CarteraVigenciaAnterior.vigencia_cartera (vigencia historica real)

SI renombra:
- ParametrosSistema.vigencia (UNIQUE - hay 1 sola row para vigencia activa)
- RubroIngreso, ContribuyentePredial, TarifaPredial, CulturaPago,
  CarteraVigenciaAnterior.vigencia_calculo, ContribuyenteICA, TarifaICA,
  Estampilla, ResumenCalculo, CifraHistoricaIngreso.vigencia_calculo,
  RubroGasto, CostoPersonal, AmortizacionPagare.vigencia_pago,
  ContratoCredito, CifraHistoricaGasto.vigencia_calculo, VigenciaFutura

Idempotente: si ya hay datos en 2027, aborta para evitar mezclar.
"""
import os
from decimal import Decimal
import django
from django.db import transaction

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'presupuesto_project.settings')
django.setup()

from core.models import ParametrosSistema, PersoneriaSMLVProgresion, VigenciaFutura
from ingresos.models import (
    RubroIngreso, ContribuyentePredial, TarifaPredial, CulturaPago,
    CarteraVigenciaAnterior, ContribuyenteICA, TarifaICA, Estampilla,
    ResumenCalculo, CifraHistoricaIngreso,
)
from gastos.models import (
    RubroGasto, CostoPersonal, AmortizacionPagare, ContratoCredito,
    CifraHistoricaGasto,
)


# Modelos a renombrar y campo donde vive la vigencia
RENAMES = [
    (ParametrosSistema,       'vigencia'),
    (VigenciaFutura,          'vigencia'),
    (RubroIngreso,            'vigencia'),
    (ContribuyentePredial,    'vigencia'),
    (TarifaPredial,           'vigencia'),
    (CulturaPago,             'vigencia'),
    (CarteraVigenciaAnterior, 'vigencia_calculo'),
    (ContribuyenteICA,        'vigencia'),
    (TarifaICA,               'vigencia'),
    (Estampilla,              'vigencia'),
    (ResumenCalculo,          'vigencia'),
    (CifraHistoricaIngreso,   'vigencia_calculo'),
    (RubroGasto,              'vigencia'),
    (CostoPersonal,           'vigencia'),
    (AmortizacionPagare,      'vigencia_pago'),
    (ContratoCredito,         'vigencia'),
    (CifraHistoricaGasto,     'vigencia_calculo'),
]

# Progresion completa Personeria por categoria (Ley 2461/2025)
# Cat 5: 210, 220, 230, 240, 250 (2025-2029)
# Cat 6: 200, 210, 220, 230, 240 (2025-2029)
PROGRESION = {
    5: {2025: 210, 2026: 220, 2027: 230, 2028: 240, 2029: 250},
    6: {2025: 200, 2026: 210, 2027: 220, 2028: 230, 2029: 240},
}


def run():
    print('== Verificando estado actual ==')
    n_2026 = ParametrosSistema.objects.filter(vigencia=2026).count()
    n_2027 = ParametrosSistema.objects.filter(vigencia=2027).count()
    print(f'ParametrosSistema  vigencia=2026: {n_2026}  vigencia=2027: {n_2027}')
    if n_2027 > 0 and n_2026 > 0:
        print('Ya existen rows con vigencia=2027 Y 2026. Aborta para no mezclar.')
        return

    print('\n== Cargando progresion Personeria cat 5 y cat 6 ==')
    for cat, mapa in PROGRESION.items():
        for vig, smlv in mapa.items():
            obj, created = PersoneriaSMLVProgresion.objects.update_or_create(
                vigencia=vig, categoria=cat, defaults={'smlv': smlv})
            estado = 'creada' if created else 'actualizada'
            print(f'  Cat {cat}  {vig}: {smlv} SMLV ({estado})')

    if n_2026 == 0:
        print('\nNo hay ParametrosSistema 2026. No hay nada que renombrar.')
        return

    with transaction.atomic():
        print('\n== Renombrando vigencia 2026 -> 2027 en todas las tablas ==')
        total_filas = 0
        for modelo, campo in RENAMES:
            n = modelo.objects.filter(**{campo: 2026}).count()
            if n == 0:
                continue
            modelo.objects.filter(**{campo: 2026}).update(**{campo: 2027})
            print(f'  {modelo.__name__}.{campo}: {n} filas')
            total_filas += n
        print(f'Total filas renombradas: {total_filas}')

    print('\n== Recalculando ingresos y gastos ==')
    from ingresos.utils import calcular_todos_ingresos
    from gastos.utils import recalcular_rubros_metodo
    calcular_todos_ingresos(2027)
    resumen = recalcular_rubros_metodo(2027)

    print('\n== Verificacion ==')
    p = ParametrosSistema.objects.filter(activo=True).first()
    print(f'  ParametrosSistema activo: vigencia={p.vigencia}')
    print(f'  Categoria municipio: {p.categoria_municipio}')

    from core.models import TablaConcejoPersoneria
    tabla = TablaConcejoPersoneria.objects.filter(categoria=p.categoria_municipio).first()
    icld = p.icld_calculado or Decimal('0')
    tc = tabla.calcular_transferencia_concejo(icld, p.valor_smlmv, p.pct_icld_adicional_concejo)
    tp = tabla.calcular_transferencia_personeria(p.vigencia, icld, p.valor_smlmv)
    print(f'  Transferencia Concejo:    ${tc:,.0f}')
    print(f'  Transferencia Personeria: ${tp:,.0f}  (cat {p.categoria_municipio}, vig {p.vigencia})')

    print(f'\n  Rubros con OCC: {resumen.get("OCC", {})}')
    print(f'  Rubros con OCP: {resumen.get("OCP", {})}')


if __name__ == '__main__':
    run()
