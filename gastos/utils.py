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


def calcular_icld(vigencia):
    """Calcula el ICLD (Ingresos Corrientes de Libre Destinación) del año
    anterior tomado de CifraHistoricaIngreso.

    ICLD = suma de los rubros marcados como ICLD del último año disponible.
    Si no hay datos retorna Decimal('0').
    """
    from ingresos.models import CifraHistoricaIngreso
    cifras = CifraHistoricaIngreso.objects.filter(vigencia_calculo=vigencia)
    ultimo_anio = cifras.values_list('anio', flat=True).order_by('-anio').first()
    if not ultimo_anio:
        return Decimal('0')
    total = cifras.filter(anio=ultimo_anio, es_icld=True).aggregate(t=Sum('valor_recaudo'))['t'] or Decimal('0')
    return total


def calcular_transferencias_organos_control(vigencia, params):
    """Aplica los métodos OCC (Concejo) y OCP (Personería) a los rubros con
    esos métodos, usando la TablaConcejoPersoneria para la categoría del
    municipio configurada en params.

    Si el ICLD del param está en 0, intenta autollenarlo desde Cifras Históricas.
    """
    from core.models import TablaConcejoPersoneria
    tabla = TablaConcejoPersoneria.objects.filter(categoria=params.categoria_municipio).first()
    if not tabla:
        return {'concejo': Decimal('0'), 'personeria': Decimal('0'),
                'rubros_concejo': 0, 'rubros_personeria': 0}

    icld = params.icld_calculado or Decimal('0')
    if icld <= 0:
        icld = calcular_icld(vigencia)

    valor_smlmv = params.valor_smlmv or Decimal('0')
    pct_adic = params.pct_icld_adicional_concejo or Decimal('0')

    transf_concejo = tabla.calcular_transferencia_concejo(icld, valor_smlmv, pct_adic)
    transf_personeria = tabla.calcular_transferencia_personeria(vigencia, icld, valor_smlmv)

    rubros_c = RubroGasto.objects.filter(vigencia=vigencia, metodo_calculo='OCC')
    rubros_p = RubroGasto.objects.filter(vigencia=vigencia, metodo_calculo='OCP')
    for r in rubros_c:
        r.valor_apropiacion = transf_concejo
        r.save(update_fields=['valor_apropiacion'])
    for r in rubros_p:
        r.valor_apropiacion = transf_personeria
        r.save(update_fields=['valor_apropiacion'])

    return {
        'concejo': transf_concejo,
        'personeria': transf_personeria,
        'rubros_concejo': rubros_c.count(),
        'rubros_personeria': rubros_p.count(),
        'icld': icld,
    }


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
               for k in ['DCAP', 'DINT', 'DTOT', 'PEN', 'CPS', 'OCC', 'OCP']}

    # Organos de control (Anexo 6): se calcula UNA vez por vigencia y se
    # aplica a todos los rubros OCC/OCP.
    from core.models import ParametrosSistema
    p = (ParametrosSistema.objects.filter(vigencia=vigencia, activo=True).first()
         or ParametrosSistema.objects.filter(vigencia=vigencia).first())
    oc_concejo = Decimal('0')
    oc_personeria = Decimal('0')
    if p:
        oc = calcular_transferencias_organos_control(vigencia, p)
        oc_concejo = oc['concejo']
        oc_personeria = oc['personeria']

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
        elif r.metodo_calculo == 'OCC':
            nuevo = oc_concejo
        elif r.metodo_calculo == 'OCP':
            nuevo = oc_personeria
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
