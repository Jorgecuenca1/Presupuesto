from decimal import Decimal
from django.db.models import Sum, Count
from core.models import ParametrosSistema
from .models import (
    TarifaPredial, CulturaPago, ContribuyentePredial, CarteraVigenciaAnterior,
    TarifaICA, ContribuyenteICA, RubroIngreso, ResumenCalculo, Estampilla,
    CATEGORIAS_URBANAS, CATEGORIAS_RURALES, TIPO_ACTIVIDAD_MAP,
)


def get_params(vigencia=None):
    if vigencia:
        return ParametrosSistema.objects.filter(vigencia=vigencia).first()
    return ParametrosSistema.objects.filter(activo=True).first()


def encontrar_tarifa_predial(avaluo, tarifas, valor_uvt):
    """Encuentra la tarifa aplicable según el avalúo catastral y rangos UVT."""
    for tarifa in tarifas:
        if tarifa.uvt_desde is not None:
            valor_desde = tarifa.uvt_desde * valor_uvt
            valor_hasta = (tarifa.uvt_hasta * valor_uvt) if tarifa.uvt_hasta else None
            if valor_hasta is None:
                if avaluo >= valor_desde:
                    return tarifa.tarifa_por_mil
            else:
                if valor_desde <= avaluo <= valor_hasta:
                    return tarifa.tarifa_por_mil
        else:
            return tarifa.tarifa_por_mil
    if tarifas.exists():
        return tarifas.last().tarifa_por_mil
    return Decimal('0')


def calcular_predial(vigencia, tipo='urbano'):
    """Calcula el impuesto predial para todos los contribuyentes de un tipo."""
    params = get_params(vigencia)
    if not params:
        return []

    if tipo == 'urbano':
        categorias = CATEGORIAS_URBANAS
    else:
        categorias = CATEGORIAS_RURALES

    ResumenCalculo.objects.filter(vigencia=vigencia, tipo=f'predial_{tipo}').delete()
    resultados = []

    pct_eficiencia_global = (params.pct_eficiencia_recaudo / Decimal('100')
                             if params.pct_eficiencia_recaudo is not None
                             else Decimal('0.70'))

    for cat in categorias:
        contribuyentes = ContribuyentePredial.objects.filter(vigencia=vigencia, categoria=cat)
        tarifas = TarifaPredial.objects.filter(vigencia=vigencia, categoria=cat).order_by('uvt_desde')
        # El % de eficiencia parametrizado es la fuente única de verdad para todas las
        # categorías. CulturaPago se mantiene como tabla histórica pero ya no se aplica.
        pct_cultura = pct_eficiencia_global

        # Factor de crecimiento viviendas aplica sólo a UV (Urbano Vivienda)
        factor_crecimiento = Decimal('1')
        if cat == 'UV':
            factor_crecimiento = Decimal('1') + (params.pct_crecimiento_viviendas or Decimal('0'))

        if tarifas.filter(uvt_desde__isnull=False).exists():
            for tarifa in tarifas:
                if tarifa.uvt_desde is not None:
                    val_desde = tarifa.uvt_desde * params.valor_uvt
                    val_hasta = (tarifa.uvt_hasta * params.valor_uvt) if tarifa.uvt_hasta else None
                    if val_hasta:
                        predios_rango = contribuyentes.filter(
                            avaluo_catastral__gte=val_desde, avaluo_catastral__lte=val_hasta
                        )
                    else:
                        predios_rango = contribuyentes.filter(avaluo_catastral__gte=val_desde)

                    for c in predios_rango:
                        c.tarifa_aplicada = tarifa.tarifa_por_mil
                        c.impuesto_calculado = c.avaluo_catastral * tarifa.tarifa_por_mil / 1000
                        c.save(update_fields=['tarifa_aplicada', 'impuesto_calculado'])

                    agg = predios_rango.aggregate(
                        total_avaluo=Sum('avaluo_catastral'),
                        cantidad=Count('id')
                    )
                    total_avaluo = agg['total_avaluo'] or 0
                    cantidad = agg['cantidad'] or 0
                    recaudo_pot = total_avaluo * tarifa.tarifa_por_mil / 1000
                    proyeccion = recaudo_pot * pct_cultura * factor_crecimiento

                    rango_desc = f'{tarifa.uvt_desde}-{tarifa.uvt_hasta or "∞"} UVT'
                    resumen = ResumenCalculo.objects.create(
                        vigencia=vigencia,
                        tipo=f'predial_{tipo}',
                        categoria=dict(ContribuyentePredial._meta.get_field('categoria').choices).get(cat, cat),
                        descripcion_rango=rango_desc,
                        total_avaluo=total_avaluo,
                        tarifa_por_mil=tarifa.tarifa_por_mil,
                        recaudo_potencial=recaudo_pot,
                        cultura_pago=pct_cultura * 100,
                        proyeccion=proyeccion,
                        cantidad_predios=cantidad,
                    )
                    resultados.append(resumen)
        else:
            tarifa = tarifas.first()
            if tarifa:
                for c in contribuyentes:
                    c.tarifa_aplicada = tarifa.tarifa_por_mil
                    c.impuesto_calculado = c.avaluo_catastral * tarifa.tarifa_por_mil / 1000
                    c.save(update_fields=['tarifa_aplicada', 'impuesto_calculado'])

                agg = contribuyentes.aggregate(
                    total_avaluo=Sum('avaluo_catastral'),
                    cantidad=Count('id')
                )
                total_avaluo = agg['total_avaluo'] or 0
                cantidad = agg['cantidad'] or 0
                recaudo_pot = total_avaluo * tarifa.tarifa_por_mil / 1000
                proyeccion = recaudo_pot * pct_cultura * factor_crecimiento

                resumen = ResumenCalculo.objects.create(
                    vigencia=vigencia,
                    tipo=f'predial_{tipo}',
                    categoria=dict(ContribuyentePredial._meta.get_field('categoria').choices).get(cat, cat),
                    descripcion_rango=tarifa.descripcion or f'Tarifa fija {tarifa.tarifa_por_mil}‰',
                    total_avaluo=total_avaluo,
                    tarifa_por_mil=tarifa.tarifa_por_mil,
                    recaudo_potencial=recaudo_pot,
                    cultura_pago=pct_cultura * 100,
                    proyeccion=proyeccion,
                    cantidad_predios=cantidad,
                )
                resultados.append(resumen)

    return resultados


def calcular_predial_vigencias_anteriores(vigencia, tipo='urbano'):
    """Calcula el predial de vigencias anteriores basado en cartera.
    Usa los porcentajes globales de ParametrosSistema (% Base Cartera, % Urbano, % Rural)."""
    params = get_params(vigencia)
    pct_base = (params.pct_cartera_base if params else Decimal('40.00'))
    if tipo == 'urbano':
        pct_tipo = (params.pct_cartera_urbano if params else Decimal('10.00'))
    else:
        pct_tipo = (params.pct_cartera_rural if params else Decimal('90.00'))

    carteras = CarteraVigenciaAnterior.objects.filter(vigencia_calculo=vigencia)
    total = Decimal('0')
    detalles = []
    for cartera in carteras:
        proy = cartera.valor_cartera * pct_base / Decimal('100') * pct_tipo / Decimal('100')
        total += proy
        detalles.append({
            'vigencia': cartera.vigencia_cartera,
            'valor_cartera': cartera.valor_cartera,
            'pct_base': pct_base,
            'pct_tipo': pct_tipo,
            'proyeccion': proy,
        })
    return total, detalles


def calcular_ica(vigencia):
    """Calcula el ICA para todos los contribuyentes agrupado por tipo."""
    params = get_params(vigencia)
    if not params:
        return {}

    ResumenCalculo.objects.filter(vigencia=vigencia, tipo='ica').delete()
    resultados = {}

    for codigo, label in ContribuyenteICA._meta.get_field('actividad').choices:
        contribuyentes = ContribuyenteICA.objects.filter(vigencia=vigencia, actividad=codigo)
        tarifa = TarifaICA.objects.filter(vigencia=vigencia, codigo_actividad=codigo).first()
        if not tarifa or not contribuyentes.exists():
            continue

        for c in contribuyentes:
            c.ingresos_proyectados = c.ingresos_brutos * (1 + params.tasa_pib_nominal)
            c.tarifa_aplicada = tarifa.tarifa_por_mil
            c.impuesto_calculado = c.ingresos_proyectados * tarifa.tarifa_por_mil / 1000
            c.save(update_fields=['tarifa_aplicada', 'impuesto_calculado', 'ingresos_proyectados'])

        agg = contribuyentes.aggregate(total_impuesto=Sum('impuesto_calculado'))
        total = agg['total_impuesto'] or 0
        tipo_act = TIPO_ACTIVIDAD_MAP.get(codigo, 'Otro')

        ResumenCalculo.objects.create(
            vigencia=vigencia,
            tipo='ica',
            categoria=label,
            descripcion_rango=f'Tarifa {tarifa.tarifa_por_mil}‰ - PIB {params.tasa_pib_nominal * 100}%',
            total_avaluo=contribuyentes.aggregate(t=Sum('ingresos_brutos'))['t'] or 0,
            tarifa_por_mil=tarifa.tarifa_por_mil,
            recaudo_potencial=total,
            cultura_pago=100,
            proyeccion=total,
            cantidad_predios=contribuyentes.count(),
        )

        if tipo_act not in resultados:
            resultados[tipo_act] = Decimal('0')
        resultados[tipo_act] += total

    return resultados


def calcular_base_estampillas(vigencia):
    """Replica la hoja 'Base Estampillas'. Retorna dict con la base y los sub-totales
    usados en el cálculo. La tarifa de cada estampilla se aplica sobre ``total_base``.

    Ítems del Excel (equivalentes):
      1  POAI Total              → params.poai_total_inversion
      2  Gasto SEV ppto NC       → params.gasto_sev_ppto_nc
      3  Saldo neto base ppto    = 1 - 2
      4  SGR                     → params.sgr_presupuesto
      5  Gasto SEV SGR           → params.gasto_sev_sgr
      6  Saldo neto base SGR     = 4 - 5         (coincide con item 82 = 6 × 72 del Excel;
                                                  la nota del libro "3 + 4 - 5" es incorrecta,
                                                  se verificó contra los valores calculados)
      71 % pagos sin SGR         → params.pct_pagos_sin_sgr
      72 % pagos SGR             → params.pct_pagos_sgr
      81 Valor base ppto sin SGR = 3 * 71
      82 Valor base ppto SGR     = 6 * 72
      9  Reservas Ppto NC        → params.reservas_presupuestales_nc
      10 Cuentas por pagar NC    → params.cuentas_por_pagar_nc
      11 Superávit Fiscal        → params.superavit_fiscal
      12 Total base cálculo      = 81 + 82 + 9 + 10 + 11
    """
    params = get_params(vigencia)
    if not params:
        return None
    poai = params.poai_total_inversion or Decimal('0')
    gasto_sev = params.gasto_sev_ppto_nc or Decimal('0')
    sgr = params.sgr_presupuesto or Decimal('0')
    gasto_sev_sgr = params.gasto_sev_sgr or Decimal('0')
    pct_sin_sgr = params.pct_pagos_sin_sgr or Decimal('0')
    pct_sgr = params.pct_pagos_sgr or Decimal('0')
    reservas = params.reservas_presupuestales_nc or Decimal('0')
    cxp = params.cuentas_por_pagar_nc or Decimal('0')
    superavit = params.superavit_fiscal or Decimal('0')

    saldo_neto_ppto = poai - gasto_sev
    saldo_neto_sgr = sgr - gasto_sev_sgr
    base_sin_sgr = saldo_neto_ppto * pct_sin_sgr
    base_sgr = saldo_neto_sgr * pct_sgr
    total_base = base_sin_sgr + base_sgr + reservas + cxp + superavit

    return {
        'poai_total': poai,
        'gasto_sev': gasto_sev,
        'saldo_neto_ppto': saldo_neto_ppto,
        'sgr': sgr,
        'gasto_sev_sgr': gasto_sev_sgr,
        'saldo_neto_sgr': saldo_neto_sgr,
        'pct_sin_sgr': pct_sin_sgr,
        'pct_sgr': pct_sgr,
        'base_sin_sgr': base_sin_sgr,
        'base_sgr': base_sgr,
        'reservas': reservas,
        'cuentas_por_pagar': cxp,
        'superavit': superavit,
        'total_base': total_base,
    }


def calcular_estampillas(vigencia):
    """Calcula la proyección anual de cada estampilla registrada.
    Retorna (total_base, [{estampilla, tarifa, proyeccion}, ...])
    y almacena un ResumenCalculo tipo 'estampilla' por cada una.
    """
    base = calcular_base_estampillas(vigencia)
    if base is None:
        return Decimal('0'), []

    ResumenCalculo.objects.filter(vigencia=vigencia, tipo='estampilla').delete()

    total_base = base['total_base']
    detalles = []
    for e in Estampilla.objects.filter(vigencia=vigencia):
        proy = total_base * e.tarifa
        ResumenCalculo.objects.create(
            vigencia=vigencia,
            tipo='estampilla',
            categoria=e.nombre,
            descripcion_rango=f'Tarifa {e.tarifa * 100:.2f}% sobre base ${float(total_base):,.0f}',
            total_avaluo=total_base,
            tarifa_por_mil=e.tarifa * 1000,
            recaudo_potencial=proy,
            cultura_pago=100,
            proyeccion=proy,
            cantidad_predios=0,
        )
        detalles.append({'estampilla': e, 'tarifa': e.tarifa, 'proyeccion': proy})
    return total_base, detalles


def calcular_todos_ingresos(vigencia):
    """Calcula todos los rubros de ingreso según su método."""
    params = get_params(vigencia)
    if not params:
        return

    # 1. Calcular predial
    calcular_predial(vigencia, 'urbano')
    calcular_predial(vigencia, 'rural')

    total_pred_urb = ResumenCalculo.objects.filter(
        vigencia=vigencia, tipo='predial_urbano'
    ).aggregate(t=Sum('proyeccion'))['t'] or 0

    total_pred_urb_ant, _ = calcular_predial_vigencias_anteriores(vigencia, 'urbano')

    total_pred_rur = ResumenCalculo.objects.filter(
        vigencia=vigencia, tipo='predial_rural'
    ).aggregate(t=Sum('proyeccion'))['t'] or 0

    total_pred_rur_ant, _ = calcular_predial_vigencias_anteriores(vigencia, 'rural')

    # 2. Calcular ICA
    ica_resultados = calcular_ica(vigencia)
    total_ica = sum(ica_resultados.values())

    # 2.5 Calcular estampillas
    total_base_est, estampillas_det = calcular_estampillas(vigencia)
    estampillas_map = {d['estampilla'].id: d['proyeccion'] for d in estampillas_det}

    # 3. Actualizar rubros según método
    rubros = RubroIngreso.objects.filter(vigencia=vigencia, es_titulo=False)
    for rubro in rubros:
        if rubro.metodo_calculo == 'PUVA':
            rubro.valor_apropiacion = total_pred_urb
        elif rubro.metodo_calculo == 'PUAN':
            rubro.valor_apropiacion = total_pred_urb_ant
        elif rubro.metodo_calculo == 'PRVA':
            rubro.valor_apropiacion = total_pred_rur
        elif rubro.metodo_calculo == 'PRAN':
            rubro.valor_apropiacion = total_pred_rur_ant
        elif rubro.metodo_calculo == 'ICAI':
            rubro.valor_apropiacion = ica_resultados.get('Industrial', 0)
        elif rubro.metodo_calculo == 'ICAC':
            rubro.valor_apropiacion = ica_resultados.get('Comercial', 0)
        elif rubro.metodo_calculo == 'ICAS':
            rubro.valor_apropiacion = ica_resultados.get('Servicios', 0)
        elif rubro.metodo_calculo == 'AT':
            rubro.valor_apropiacion = total_ica * Decimal('0.15')
        elif rubro.metodo_calculo == 'IPC':
            rubro.valor_apropiacion = rubro.recaudo_vigencia_anterior * (1 + params.tasa_ipc)
        elif rubro.metodo_calculo == 'ICN':
            rubro.valor_apropiacion = rubro.recaudo_vigencia_anterior * (1 + params.tasa_icn)
        elif rubro.metodo_calculo == 'POAI':
            if rubro.tarifa_poai:
                rubro.valor_apropiacion = params.poai_total_inversion * rubro.tarifa_poai
        elif rubro.metodo_calculo == 'EST':
            if rubro.estampilla_id and rubro.estampilla_id in estampillas_map:
                rubro.valor_apropiacion = estampillas_map[rubro.estampilla_id]
                rubro.observaciones = 'Base calculo estampillas * tarifa Estatuto tributario'
                rubro.save(update_fields=['valor_apropiacion', 'observaciones'])
                continue
        # MAN = manual, no se cambia
        rubro.save(update_fields=['valor_apropiacion'])

    # 4. Recalcular títulos/subtotales de abajo hacia arriba
    titulos = RubroIngreso.objects.filter(vigencia=vigencia, es_titulo=True).order_by('-nivel')
    for titulo in titulos:
        titulo.calcular_hijos()
