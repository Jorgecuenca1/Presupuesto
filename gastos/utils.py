"""Utilidades de cálculo para gastos.

Recalcula los rubros según su `metodo_calculo`:
  DCAP / DINT / DTOT  → suma de las amortizaciones de los pagarés en la vigencia.
  PEN                  → costo total de los CostoPersonal con es_pensionado=True.
  CPS                  → costo total de los CostoPersonal de la sección del rubro.
  MAN                  → no se modifica.

La función nunca borra registros; sólo reescribe ``valor_apropiacion`` de los
rubros con método automático y luego propaga los títulos.
"""
from decimal import Decimal

from django.db.models import Sum

from .models import (
    RubroGasto, ContratoCredito, AmortizacionPagare, CostoPersonal,
    SeccionGasto,
)


def _suma_amortizaciones(vigencia, campo):
    """campo ∈ {capital_principal, intereses, intereses_tcr, total}."""
    qs = AmortizacionPagare.objects.filter(vigencia_pago=vigencia)
    if campo == 'total':
        # total = capital + intereses + intereses_tcr
        agg = qs.aggregate(
            c=Sum('capital_principal'),
            i=Sum('intereses'),
            t=Sum('intereses_tcr'),
        )
        return (agg['c'] or Decimal('0')) + (agg['i'] or Decimal('0')) + (agg['t'] or Decimal('0'))
    return qs.aggregate(t=Sum(campo))['t'] or Decimal('0')


def _suma_pensionados(vigencia):
    """Costo total anual de personal pensionado en la vigencia."""
    total = Decimal('0')
    for p in CostoPersonal.objects.filter(vigencia=vigencia, es_pensionado=True):
        total += p.costo_total_anual
    return total


def _suma_costo_personal_seccion(vigencia, seccion_id):
    """Costo total anual del personal activo de una sección."""
    if not seccion_id:
        return Decimal('0')
    total = Decimal('0')
    for p in CostoPersonal.objects.filter(vigencia=vigencia, es_pensionado=False,
                                           seccion_id=seccion_id):
        total += p.costo_total_anual
    return total


def recalcular_rubros_metodo(vigencia):
    """Aplica el método de cálculo a cada RubroGasto y devuelve un resumen.

    Resumen:
        {
            'DCAP': {'rubros': N, 'total_aplicado': Decimal},
            'DINT': ..., 'DTOT': ..., 'PEN': ..., 'CPS': ...
        }
    """
    cap = _suma_amortizaciones(vigencia, 'capital_principal')
    inter = _suma_amortizaciones(vigencia, 'intereses')
    total_deu = _suma_amortizaciones(vigencia, 'total')
    pens = _suma_pensionados(vigencia)

    resumen = {k: {'rubros': 0, 'total_aplicado': Decimal('0')}
               for k in ['DCAP', 'DINT', 'DTOT', 'PEN', 'CPS']}

    rubros = (RubroGasto.objects
              .filter(vigencia=vigencia, es_titulo=False)
              .exclude(metodo_calculo='MAN'))

    for r in rubros:
        nuevo = None
        if r.metodo_calculo == 'DCAP':
            nuevo = cap
        elif r.metodo_calculo == 'DINT':
            nuevo = inter
        elif r.metodo_calculo == 'DTOT':
            nuevo = total_deu
        elif r.metodo_calculo == 'PEN':
            nuevo = pens
        elif r.metodo_calculo == 'CPS':
            nuevo = _suma_costo_personal_seccion(vigencia, r.seccion_id)
        if nuevo is None:
            continue
        r.valor_apropiacion = nuevo
        r.save(update_fields=['valor_apropiacion'])
        resumen[r.metodo_calculo]['rubros'] += 1
        resumen[r.metodo_calculo]['total_aplicado'] += nuevo

    # Propagar títulos
    titulos = RubroGasto.objects.filter(vigencia=vigencia, es_titulo=True).order_by('-nivel')
    for titulo in titulos:
        titulo.calcular_hijos()

    return resumen
