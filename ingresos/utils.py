from decimal import Decimal
from django.db.models import Sum, Count
from core.models import ParametrosSistema
from .models import (
    TarifaPredial, CulturaPago, ContribuyentePredial, CarteraVigenciaAnterior,
    TarifaICA, ContribuyenteICA, RubroIngreso, ResumenCalculo,
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

    for cat in categorias:
        contribuyentes = ContribuyentePredial.objects.filter(vigencia=vigencia, categoria=cat)
        tarifas = TarifaPredial.objects.filter(vigencia=vigencia, categoria=cat).order_by('uvt_desde')
        cultura = CulturaPago.objects.filter(vigencia=vigencia, categoria=cat).first()
        pct_cultura = cultura.porcentaje / 100 if cultura else Decimal('0.70')

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
                    proyeccion = recaudo_pot * pct_cultura

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
                proyeccion = recaudo_pot * pct_cultura

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
    """Calcula el predial de vigencias anteriores basado en cartera."""
    carteras = CarteraVigenciaAnterior.objects.filter(vigencia_calculo=vigencia)
    total = Decimal('0')
    detalles = []
    for cartera in carteras:
        if tipo == 'urbano':
            proy = cartera.proyeccion_urbano
        else:
            proy = cartera.proyeccion_rural
        total += proy
        detalles.append({
            'vigencia': cartera.vigencia_cartera,
            'valor_cartera': cartera.valor_cartera,
            'pct_base': cartera.porcentaje_base,
            'pct_tipo': cartera.porcentaje_urbano if tipo == 'urbano' else cartera.porcentaje_rural,
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
        # MAN = manual, no se cambia
        rubro.save(update_fields=['valor_apropiacion'])

    # 4. Recalcular títulos/subtotales de abajo hacia arriba
    titulos = RubroIngreso.objects.filter(vigencia=vigencia, es_titulo=True).order_by('-nivel')
    for titulo in titulos:
        titulo.calcular_hijos()
