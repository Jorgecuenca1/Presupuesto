from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.db.models import Sum, Count
from decimal import Decimal
from .forms import LoginForm, RegistroForm, ParametrosForm, TablaConcejoPersoneriaForm
from .models import (
    ParametrosSistema, TablaConcejoPersoneria, PersoneriaSMLVProgresion,
    VariableMacro, TechoInversion,
)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data['username'],
                                password=form.cleaned_data['password'])
            if user:
                login(request, user)
                return redirect('dashboard')
            messages.error(request, 'Usuario o contraseña incorrectos')
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})


def register_view(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Cuenta creada exitosamente')
            return redirect('dashboard')
    else:
        form = RegistroForm()
    return render(request, 'core/register.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    from ingresos.models import ContribuyentePredial, ContribuyenteICA, RubroIngreso, ResumenCalculo
    from gastos.models import RubroGasto
    params = ParametrosSistema.objects.filter(activo=True).first()
    vigencia = params.vigencia if params else 2026

    total_contribuyentes_predial = ContribuyentePredial.objects.filter(vigencia=vigencia).count()
    total_contribuyentes_ica = ContribuyenteICA.objects.filter(vigencia=vigencia).count()

    # Total ingresos = suma de rubros HOJA (es_titulo=False). Más confiable que
    # depender de que los títulos nivel 0 estén recalculados.
    total_ingresos = RubroIngreso.objects.filter(
        vigencia=vigencia, es_titulo=False
    ).aggregate(total=Sum('valor_apropiacion'))['total'] or 0

    # Total gastos = suma de rubros HOJA
    total_gastos = RubroGasto.objects.filter(
        vigencia=vigencia, es_titulo=False
    ).aggregate(total=Sum('valor_apropiacion'))['total'] or 0

    # Equilibrio
    equilibrio = Decimal(str(total_ingresos)) - Decimal(str(total_gastos))

    # Componentes de ingresos (suma de proyecciones por tipo en ResumenCalculo)
    total_predial_va = ResumenCalculo.objects.filter(
        vigencia=vigencia, tipo__in=['predial_urbano', 'predial_rural']
    ).aggregate(t=Sum('proyeccion'))['t'] or Decimal('0')
    # Sumar predial de vigencias anteriores (cobranza atrasada) para que coincida con /ingresos/calculo-predial/
    try:
        from ingresos.utils import calcular_predial_vigencias_anteriores
        total_urb_ant, _ = calcular_predial_vigencias_anteriores(vigencia, 'urbano')
        total_rur_ant, _ = calcular_predial_vigencias_anteriores(vigencia, 'rural')
        total_predial = total_predial_va + (total_urb_ant or Decimal('0')) + (total_rur_ant or Decimal('0'))
    except Exception:
        total_predial = total_predial_va
    total_ica_calc = ResumenCalculo.objects.filter(
        vigencia=vigencia, tipo='ica'
    ).aggregate(t=Sum('proyeccion'))['t'] or Decimal('0')
    total_estampillas_calc = ResumenCalculo.objects.filter(
        vigencia=vigencia, tipo='estampilla'
    ).aggregate(t=Sum('proyeccion'))['t'] or Decimal('0')

    # Gastos por tipo
    total_funcionamiento = RubroGasto.objects.filter(
        vigencia=vigencia, tipo_gasto='FUN', es_titulo=False
    ).aggregate(t=Sum('valor_apropiacion'))['t'] or 0
    total_inversion = RubroGasto.objects.filter(
        vigencia=vigencia, tipo_gasto='INV', es_titulo=False
    ).aggregate(t=Sum('valor_apropiacion'))['t'] or 0
    total_deuda = RubroGasto.objects.filter(
        vigencia=vigencia, tipo_gasto='DEU', es_titulo=False
    ).aggregate(t=Sum('valor_apropiacion'))['t'] or 0

    rubros_por_metodo = RubroIngreso.objects.filter(
        vigencia=vigencia, es_titulo=False
    ).exclude(metodo_calculo='MAN').values('metodo_calculo').annotate(
        total=Sum('valor_apropiacion'), cantidad=Count('id')
    ).order_by('-total')

    # Indicador Ley 617 (si hay datos)
    indicador_617 = Decimal('0')
    if params and total_funcionamiento > 0:
        from ingresos.models import CifraHistoricaIngreso
        cifras_ing = CifraHistoricaIngreso.objects.filter(vigencia_calculo=vigencia)
        ultimo_anio = cifras_ing.values_list('anio', flat=True).order_by('-anio').first()
        if ultimo_anio:
            icld = cifras_ing.filter(anio=ultimo_anio, es_icld=True).aggregate(t=Sum('valor_recaudo'))['t'] or Decimal('0')
            sgp_libre = cifras_ing.filter(anio=ultimo_anio, es_sgp_libre=True).aggregate(t=Sum('valor_recaudo'))['t'] or Decimal('0')
            icld_total = icld + sgp_libre
            if icld_total > 0:
                indicador_617 = (Decimal(str(total_funcionamiento)) / icld_total * 100).quantize(Decimal('0.01'))

    # ── MFMP Nación 2026: variables macroeconómicas por año ────────────
    from .models import VariableMacro
    MFMP_TIPOS = [
        ('PIB_R', 'Crecimiento PIB real', '%'),
        ('PIB_N', 'Crecimiento PIB nominal', '%'),
        ('SOCIOS', 'Socios comerciales', '%'),
        ('CTA_CORR', 'Balance cta. corriente', '% PIB'),
        ('TRM', 'TRM promedio', 'USD/COP'),
        ('DEPREC', 'Depreciación TRM', '%'),
        ('PETROLEO', 'Precio Brent', 'USD'),
        ('PROD_PET', 'Producción petróleo', 'KBPD'),
        ('IPC', 'Inflación fin periodo', '%'),
        ('ING_GNC', 'Ingresos GNC', '% PIB'),
        ('GTO_GNC', 'Gastos GNC', '% PIB'),
        ('BAL_GNC', 'Balance fiscal GNC', '% PIB'),
        ('BAL_PRIM', 'Balance primario GNC', '% PIB'),
        ('T_LOCAL', 'Tasa interés local', '%'),
        ('T_EXT', 'Tasa interés externa', '%'),
        ('D_NETA', 'Deuda neta GNC', '% PIB'),
        ('BAL_GG', 'Balance fiscal GG', '% PIB'),
        ('D_GG', 'Deuda consolidada GG', '% PIB'),
    ]
    vig = params.vigencia if params else 2027
    mfmp_anios = list(range(vig, vig + 11))  # 11 años a partir de vigencia
    mfmp_data = {t[0]: {} for t in MFMP_TIPOS}
    for vm in VariableMacro.objects.filter(tipo__in=[t[0] for t in MFMP_TIPOS], anio__in=mfmp_anios):
        mfmp_data[vm.tipo][vm.anio] = vm.valor
    mfmp_tabla = []
    for cod, nombre, unidad in MFMP_TIPOS:
        fila = {'codigo': cod, 'nombre': nombre, 'unidad': unidad,
                'valores': [mfmp_data.get(cod, {}).get(a) for a in mfmp_anios]}
        # Solo incluir si tiene al menos un dato
        if any(v is not None for v in fila['valores']):
            mfmp_tabla.append(fila)

    context = {
        'params': params,
        'total_contribuyentes_predial': total_contribuyentes_predial,
        'total_contribuyentes_ica': total_contribuyentes_ica,
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'equilibrio': equilibrio,
        'total_predial': total_predial,
        'total_ica_calc': total_ica_calc,
        'total_estampillas_calc': total_estampillas_calc,
        'total_funcionamiento': total_funcionamiento,
        'total_inversion': total_inversion,
        'total_deuda': total_deuda,
        'rubros_por_metodo': rubros_por_metodo,
        'indicador_617': indicador_617,
        'mfmp_anios': mfmp_anios,
        'mfmp_tabla': mfmp_tabla,
    }
    return render(request, 'core/dashboard.html', context)


def _regenerar_componentes_cargo(cp, params, actualizar_salario=False):
    """Regenera prestaciones, aportes, parafiscales y override de UN cargo usando
    su salario_basico actual y los % de params.

    Args:
      cp: instancia CostoPersonal
      params: ParametrosSistema
      actualizar_salario: si True, recalcula salario_basico desde anterior × (1+%)
                          aplicando pct_incremento_salarial de params.
                          Si False, respeta el salario_basico actual del cargo.
    """
    from decimal import Decimal as _D
    if cp.es_pensionado:
        if cp.salario_basico_anterior and cp.salario_basico_anterior > 0:
            incr = _D('1') + (params.pct_incremento_pensionados or _D('0'))
            cp.salario_basico = (cp.salario_basico_anterior * incr).quantize(_D('0.01'))
            cp.pct_incremento = params.pct_incremento_pensionados or _D('0')
            cp.costo_total_anual_override = (cp.salario_basico * 14).quantize(_D('0.01'))
            cp.save(update_fields=['salario_basico', 'pct_incremento', 'costo_total_anual_override'])
        return

    if actualizar_salario and cp.salario_basico_anterior and cp.salario_basico_anterior > 0:
        pct_incr = params.pct_incremento_salarial or _D('0')
        cp.pct_incremento = pct_incr
        cp.salario_basico = (cp.salario_basico_anterior * (_D('1') + pct_incr)).quantize(_D('0.01'))

    sal_mes = cp.salario_basico or _D('0')
    sal_anual = sal_mes * 12
    cant = _D(cp.cantidad)

    # Prestaciones
    cp.prima_servicios = sal_anual * (params.pct_prima_servicios or 0)
    cp.prima_navidad = sal_anual * (params.pct_prima_navidad or 0)
    cp.prima_vacaciones = sal_anual * (params.pct_prima_vacaciones or 0)
    cp.vacaciones = sal_anual * _D('0.0417')
    cp.cesantias = sal_anual * (params.pct_cesantias or 0)
    cp.intereses_cesantias = cp.cesantias * (params.pct_intereses_cesantias or 0)
    # BSP por umbral
    umbral_bsp = (params.umbral_smlmv_bsp or _D('2.0')) * (params.valor_smlmv or _D('0'))
    if sal_mes <= umbral_bsp:
        pct_bsp = params.pct_bonif_servicios_prestados or _D('0.50')
    else:
        pct_bsp = params.pct_bonif_servicios_prestados_alto or _D('0.35')
    cp.bonif_servicios_prestados = sal_mes * pct_bsp
    cp.bonif_recreacion = sal_anual * (params.pct_bonif_recreacion or 0)
    # Aportes
    cp.aportes_pension = sal_anual * (params.pct_aporte_pension or 0)
    cp.aportes_salud = sal_anual * (params.pct_aporte_salud or 0)
    cp.aportes_arl = sal_anual * (params.pct_aporte_arl or 0)
    cp.aportes_sena = sal_anual * (params.pct_aporte_sena or 0)
    cp.aportes_icbf = sal_anual * (params.pct_aporte_icbf or 0)
    cp.aportes_caja = sal_anual * (params.pct_aporte_caja or 0)
    cp.aportes_esap = sal_anual * (params.pct_aporte_esap or 0)
    cp.aportes_escuelas = sal_anual * (params.pct_aporte_escuelas or 0)
    # Subsidio transporte si sal <= 2 SMLMV
    if params.valor_smlmv and sal_mes <= (2 * params.valor_smlmv):
        cp.subsidio_transporte_anual = (params.subsidio_transporte_mensual or 0) * 12
    else:
        cp.subsidio_transporte_anual = _D('0')

    suma = (sal_anual + cp.prima_servicios + cp.prima_navidad + cp.prima_vacaciones +
            cp.vacaciones + cp.cesantias + cp.intereses_cesantias +
            cp.bonif_servicios_prestados + cp.bonif_recreacion +
            cp.bonif_direccion + cp.bonif_territorial +
            cp.aportes_pension + cp.aportes_salud + cp.aportes_arl +
            cp.aportes_sena + cp.aportes_icbf + cp.aportes_caja +
            cp.aportes_esap + cp.aportes_escuelas +
            cp.subsidio_transporte_anual)
    cp.costo_total_anual_override = suma * cant
    cp.save()


def _regenerar_costo_personal(params):
    """Regenera TODOS los CostoPersonal de la vigencia activa usando los %
    legales de ParametrosSistema. Actualiza salario_basico desde el % global.
    """
    from decimal import Decimal as _D
    from gastos.models import CostoPersonal
    vig = params.vigencia
    pct_incr_salarial = params.pct_incremento_salarial or _D('0')

    for cp in CostoPersonal.objects.filter(vigencia=vig, es_pensionado=False):
        # 1) PRIMERO: actualizar salario_basico desde anterior × (1 + % incremento)
        # para que el cambio en pct_incremento_salarial se propague automaticamente.
        if cp.salario_basico_anterior and cp.salario_basico_anterior > 0:
            cp.pct_incremento = pct_incr_salarial
            cp.salario_basico = (cp.salario_basico_anterior * (_D('1') + pct_incr_salarial)).quantize(_D('0.01'))

        sal_mes = cp.salario_basico or _D('0')
        sal_anual = sal_mes * 12
        cant = _D(cp.cantidad)
        # Prestaciones (anual por persona)
        cp.prima_servicios = sal_anual * (params.pct_prima_servicios or 0)
        cp.prima_navidad = sal_anual * (params.pct_prima_navidad or 0)
        cp.prima_vacaciones = sal_anual * (params.pct_prima_vacaciones or 0)
        cp.vacaciones = sal_anual * _D('0.0417')
        cp.cesantias = sal_anual * (params.pct_cesantias or 0)
        cp.intereses_cesantias = cp.cesantias * (params.pct_intereses_cesantias or 0)
        # BSP (Bonificacion por Servicios Prestados) - Dto 1042/78 art. 45:
        # - Si salario_mensual <= umbral × SMLMV: BSP = 50% del sueldo (sueldo bajo)
        # - Si salario_mensual >  umbral × SMLMV: BSP = 35% del sueldo (sueldo alto)
        umbral_bsp = (params.umbral_smlmv_bsp or _D('2.0')) * (params.valor_smlmv or _D('0'))
        if sal_mes <= umbral_bsp:
            pct_bsp = params.pct_bonif_servicios_prestados or _D('0.50')
        else:
            pct_bsp = params.pct_bonif_servicios_prestados_alto or _D('0.35')
        cp.bonif_servicios_prestados = sal_mes * pct_bsp
        cp.bonif_recreacion = sal_anual * (params.pct_bonif_recreacion or 0)
        # Aportes seguridad social
        cp.aportes_pension = sal_anual * (params.pct_aporte_pension or 0)
        cp.aportes_salud = sal_anual * (params.pct_aporte_salud or 0)
        cp.aportes_arl = sal_anual * (params.pct_aporte_arl or 0)
        # Parafiscales
        cp.aportes_sena = sal_anual * (params.pct_aporte_sena or 0)
        cp.aportes_icbf = sal_anual * (params.pct_aporte_icbf or 0)
        cp.aportes_caja = sal_anual * (params.pct_aporte_caja or 0)
        cp.aportes_esap = sal_anual * (params.pct_aporte_esap or 0)
        cp.aportes_escuelas = sal_anual * (params.pct_aporte_escuelas or 0)
        # Subsidio transporte (Ley 15/1959) si salario <= 2 SMLMV
        if params.valor_smlmv and sal_mes <= (2 * params.valor_smlmv):
            cp.subsidio_transporte_anual = (params.subsidio_transporte_mensual or 0) * 12
        else:
            cp.subsidio_transporte_anual = _D('0')

        suma_componentes = (sal_anual + cp.prima_servicios + cp.prima_navidad +
                            cp.prima_vacaciones + cp.vacaciones + cp.cesantias +
                            cp.intereses_cesantias + cp.bonif_servicios_prestados +
                            cp.bonif_recreacion + cp.bonif_direccion + cp.bonif_territorial +
                            cp.aportes_pension + cp.aportes_salud + cp.aportes_arl +
                            cp.aportes_sena + cp.aportes_icbf + cp.aportes_caja +
                            cp.aportes_esap + cp.aportes_escuelas +
                            cp.subsidio_transporte_anual)
        cp.costo_total_anual_override = suma_componentes * cant
        cp.save()

    # Pensionados: aplicar incremento mesada
    for cp in CostoPersonal.objects.filter(vigencia=vig, es_pensionado=True):
        if cp.salario_basico_anterior and cp.salario_basico_anterior > 0:
            incr = _D('1') + (params.pct_incremento_pensionados or _D('0'))
            cp.salario_basico = (cp.salario_basico_anterior * incr).quantize(_D('0.01'))
            cp.pct_incremento = params.pct_incremento_pensionados or _D('0')
            cp.costo_total_anual_override = (cp.salario_basico * 14).quantize(_D('0.01'))
            cp.save(update_fields=['salario_basico', 'pct_incremento', 'costo_total_anual_override'])

    # Deuda: recomputar intereses_tcr de TODAS las amortizaciones con el nuevo TCR
    from gastos.models import AmortizacionPagare
    tcr = params.tcr_deuda or _D('0.921')
    for a in AmortizacionPagare.objects.all():
        nuevo_tcr = (a.intereses * tcr).quantize(_D('0.01'))
        if a.intereses_tcr != nuevo_tcr:
            a.intereses_tcr = nuevo_tcr
            a.save(update_fields=['intereses_tcr'])



def _recalcular_titulos_por_codigo(vigencia):
    """Recalcula el valor de cada rubro titulo de gasto sumando las hojas
    descendientes por prefijo de codigo. Necesario porque el parent FK no
    esta siempre seteado en RubroGasto."""
    from gastos.models import RubroGasto
    todos = list(RubroGasto.objects.filter(vigencia=vigencia))
    hojas = {(r.seccion_id, r.codigo): r.valor_apropiacion
             for r in todos if not r.es_titulo and r.codigo}
    for t in todos:
        if not t.es_titulo or not t.codigo:
            continue
        pref = t.codigo + '.'
        suma = sum(v for (sec, cod), v in hojas.items()
                   if sec == t.seccion_id and cod.startswith(pref))
        if t.valor_apropiacion != suma:
            t.valor_apropiacion = suma
            t.save(update_fields=['valor_apropiacion'])


def _distribuir_componentes_rubros(vigencia):
    """Distribuye componentes de CostoPersonal a los rubros CUIPO detalle del Anexo 2.

    Necesario para que al cambiar % en Parametros, no solo el rubro padre 2.1.1.01
    (con metodo CPS) se actualice sino tambien sus hijos individuales (Sueldo basico,
    Prima navidad, Aportes salud, etc.) que de otra forma quedan estaticos.
    """
    from gastos.models import CostoPersonal, RubroGasto, SeccionGasto
    MAPEO = {
        '2.1.1.01.01.001.01':    lambda cp: cp.salario_basico * 12 * cp.cantidad,
        '2.1.1.01.01.001.06':    lambda cp: cp.prima_servicios * cp.cantidad,
        '2.1.1.01.01.001.07':    lambda cp: cp.bonif_servicios_prestados * cp.cantidad,
        '2.1.1.01.01.001.08.01': lambda cp: cp.prima_navidad * cp.cantidad,
        '2.1.1.01.01.001.08.02': lambda cp: cp.prima_vacaciones * cp.cantidad,
        '2.1.1.01.02.001':       lambda cp: cp.aportes_pension * cp.cantidad,
        '2.1.1.01.02.002':       lambda cp: cp.aportes_salud * cp.cantidad,
        '2.1.1.01.02.003':       lambda cp: cp.cesantias * cp.cantidad,
        '2.1.1.01.02.004':       lambda cp: cp.aportes_caja * cp.cantidad,
        '2.1.1.01.02.005':       lambda cp: cp.aportes_arl * cp.cantidad,
        '2.1.1.01.02.006':       lambda cp: cp.aportes_icbf * cp.cantidad,
        '2.1.1.01.02.007':       lambda cp: cp.aportes_sena * cp.cantidad,
        '2.1.1.01.02.008':       lambda cp: cp.aportes_esap * cp.cantidad,
        '2.1.1.01.02.009':       lambda cp: cp.aportes_escuelas * cp.cantidad,
        '2.1.1.01.03.001.01':    lambda cp: cp.vacaciones * cp.cantidad,
        '2.1.1.01.03.001.03':    lambda cp: cp.bonif_recreacion * cp.cantidad,
    }
    for sec in SeccionGasto.objects.all():
        cargos = list(CostoPersonal.objects.filter(vigencia=vigencia, seccion=sec, es_pensionado=False))
        if not cargos:
            continue
        for codigo, fn in MAPEO.items():
            valor = sum(fn(cp) for cp in cargos)
            RubroGasto.objects.filter(
                vigencia=vigencia, seccion=sec, codigo=codigo, es_titulo=False
            ).update(valor_apropiacion=valor)

def _limpiar_cop(post_data, campos):
    """Quita puntos de campos monetarios para parsearlos como Decimal."""
    if not hasattr(post_data, '_mutable'):
        return post_data
    post_data._mutable = True
    for campo in campos:
        if campo in post_data and post_data[campo]:
            post_data[campo] = post_data[campo].replace('.', '').replace(',', '.')
    post_data._mutable = False
    return post_data


def _limite_ley617_por_categoria(cat):
    """Ley 617/2000 art. 6: % límite gastos funcionamiento sobre ICLD."""
    mapa = {'E': 50, '1': 65, '2': 70, '3': 70, '4': 80, '5': 80, '6': 80}
    return Decimal(str(mapa.get(str(cat or '5').strip().upper(), 80)))


def _sincronizar_params_desde_macro(params):
    """Sincroniza SMLMV, IPC, UVT, pct_incremento_pensionados y límites
    legales de un ParametrosSistema con los valores de VariableMacro y las
    normas vigentes. Se llama tanto en GET como en POST del form.

    Retorna dict con lo que cambió (para telemetría/log).
    """
    from .models import get_smlv, get_ipc
    cambios = {}
    if not params:
        return cambios
    vig = params.vigencia

    # SMLMV desde Variables Macro
    smlv = get_smlv(vig)
    if smlv and smlv > 0 and params.valor_smlmv != smlv:
        cambios['valor_smlmv'] = (params.valor_smlmv, smlv)
        params.valor_smlmv = smlv

    smlv_obj = VariableMacro.objects.filter(anio=vig, tipo='SMLV').first()
    if smlv_obj and smlv_obj.pct_anual and params.pct_incremento_salarial != smlv_obj.pct_anual:
        cambios['pct_incremento_salarial'] = (params.pct_incremento_salarial, smlv_obj.pct_anual)
        params.pct_incremento_salarial = smlv_obj.pct_anual

    # IPC + derivados
    ipc = get_ipc(vig)
    if ipc and ipc > 0:
        if params.tasa_ipc != ipc:
            cambios['tasa_ipc'] = (params.tasa_ipc, ipc)
            params.tasa_ipc = ipc
        # % incremento pensionados = IPC (Ley 100/1993 art. 14)
        if params.pct_incremento_pensionados != ipc:
            cambios['pct_incremento_pensionados'] = (params.pct_incremento_pensionados, ipc)
            params.pct_incremento_pensionados = ipc

        # UVT proyectada = UVT_año_anterior × (1 + IPC_vigencia)
        uvt_prev = VariableMacro.objects.filter(anio=vig - 1, tipo='UVT').first()
        if uvt_prev and uvt_prev.valor > 0:
            uvt_proj = (uvt_prev.valor * (Decimal('1') + ipc)).quantize(Decimal('1'))
            if params.valor_uvt != uvt_proj:
                cambios['valor_uvt'] = (params.valor_uvt, uvt_proj)
                params.valor_uvt = uvt_proj
            VariableMacro.objects.update_or_create(
                anio=vig, tipo='UVT',
                defaults={'valor': uvt_proj, 'pct_anual': ipc, 'es_proyectado': True},
            )

    # Ley 358/1997 actualizada por Ley 819/2003:
    #   Solvencia (intereses / ahorro operacional) máx 40% → sostenibilidad
    #   Sostenibilidad (saldo deuda / ingresos corrientes) máx 80% → sostenibilidad
    # Ley 1416/2010 y decreto 707/2013 subieron indicadores a 60% y 100%
    # respectivamente para municipios cat 4-6
    if params.pct_limite_intereses_ley358 != Decimal('60'):
        cambios['pct_limite_intereses_ley358'] = (params.pct_limite_intereses_ley358, Decimal('60'))
        params.pct_limite_intereses_ley358 = Decimal('60')
    if params.pct_limite_saldo_deuda_ley358 != Decimal('100'):
        cambios['pct_limite_saldo_deuda_ley358'] = (params.pct_limite_saldo_deuda_ley358, Decimal('100'))
        params.pct_limite_saldo_deuda_ley358 = Decimal('100')

    # Ley 617/2000 art. 6: límite gasto funcionamiento según categoría
    lim617 = _limite_ley617_por_categoria(params.categoria_municipio)
    if params.pct_limite_funcionamiento_ley617 != lim617:
        cambios['pct_limite_funcionamiento_ley617'] = (
            params.pct_limite_funcionamiento_ley617, lim617)
        params.pct_limite_funcionamiento_ley617 = lim617

    if cambios:
        params.save()
    return cambios


@never_cache
@login_required
def parametros_view(request):
    params = ParametrosSistema.objects.filter(activo=True).first()
    if not params:
        params = ParametrosSistema.objects.order_by('-vigencia').first()

    # Sincronización perezosa: al abrir el form ya trae los valores oficiales
    # (SMLMV, IPC, UVT proyectada, límites legales, % pensionados = IPC).
    try:
        _sincronizar_params_desde_macro(params)
    except Exception:
        pass

    # Autollenar ICLD si esta en 0 y hay cifras historicas
    if params and (params.icld_calculado is None or params.icld_calculado == 0):
        from gastos.utils import calcular_icld
        icld_auto = calcular_icld(params.vigencia)
        if icld_auto > 0:
            params.icld_calculado = icld_auto

    if request.method == 'POST':
        _MONETARIOS_PARAMS = [
            'icld_calculado','valor_smlmv','valor_uvt','subsidio_transporte_mensual',
            'poai_total_inversion','gasto_sev_ppto_nc','sgr_presupuesto','gasto_sev_sgr',
            'reservas_presupuestales_nc','cuentas_por_pagar_nc','superavit_fiscal',
            'recaudo_oleoductos_anio_n3','recaudo_oleoductos_anio_n2','recaudo_oleoductos_anio_n1',
        ]
        _limpiar_cop(request.POST, _MONETARIOS_PARAMS)
        form = ParametrosForm(request.POST, instance=params)
        if form.is_valid():
            params_saved = form.save(commit=False)
            params_saved.activo = True
            # Sincronización automática (SMLMV, IPC, UVT, % pensionados, límites Ley 358 y 617)
            params_saved.save()
            _sincronizar_params_desde_macro(params_saved)

            # Recalcular ingresos y gastos con los nuevos parámetros
            from ingresos.utils import calcular_todos_ingresos
            from ingresos.models import RubroIngreso
            from gastos.models import RubroGasto, CostoPersonal
            from gastos.utils import recalcular_rubros_metodo
            try:
                calcular_todos_ingresos(params_saved.vigencia)
                # Regenerar CostoPersonal con los % nuevos de Parametros (recursivo)
                _regenerar_costo_personal(params_saved)
                _distribuir_componentes_rubros(params_saved.vigencia)
                recalcular_rubros_metodo(params_saved.vigencia)
                titulos_ing = RubroIngreso.objects.filter(
                    vigencia=params_saved.vigencia, es_titulo=True
                ).order_by('-nivel')
                for t in titulos_ing:
                    t.calcular_hijos()
                _recalcular_titulos_por_codigo(params_saved.vigencia)
                messages.success(
                    request,
                    f'Parámetros guardados y rubros recalculados para vigencia {params_saved.vigencia}'
                )
            except Exception as e:
                messages.warning(
                    request,
                    f'Parámetros guardados, pero el recálculo falló: {e}'
                )
            return redirect('parametros')
        else:
            messages.error(request, f'Revisa los errores del formulario: {form.errors.as_text()}')
    else:
        form = ParametrosForm(instance=params)
    return render(request, 'ingresos/parametros_form.html', {'form': form, 'params': params})


@never_cache
@login_required
def tabla_concejo_personeria(request):
    """Anexo 6 - Organos de Control.

    GET: Tabla integral editable por categoria municipal con valores calculados.
    POST: Guarda los cambios de Variables base + Tabla por categoria + Progresion
          SMLV, y recalcula todos los rubros automaticos (OCC, OCP, CPS, PEN, etc.).
    """
    form = TablaConcejoPersoneriaForm()
    params = ParametrosSistema.objects.filter(activo=True).first()

    if request.method == 'POST' and params:
        try:
            # Limpiar puntos COP de campos monetarios
            if hasattr(request.POST, '_mutable'):
                request.POST._mutable = True
                for k in ['icld_calculado', 'valor_smlmv']:
                    if k in request.POST and request.POST[k]:
                        request.POST[k] = request.POST[k].replace('.', '').replace(',', '.')
                request.POST._mutable = False
            # 1. Variables base (ParametrosSistema)
            # NOTA: valor_smlmv NO se acepta del form (readonly), siempre se sincroniza desde Variables Macro
            from .models import get_smlv, get_ipc, VariableMacro
            smlv_vig = get_smlv(params.vigencia)
            if smlv_vig and smlv_vig > 0:
                params.valor_smlmv = smlv_vig
            if False and 'valor_smlmv' in request.POST:
                params.valor_smlmv = Decimal(request.POST['valor_smlmv'] or '0')
            if 'icld_calculado' in request.POST:
                params.icld_calculado = Decimal(request.POST['icld_calculado'] or '0')
            if 'pct_icld_adicional_concejo' in request.POST:
                params.pct_icld_adicional_concejo = Decimal(
                    request.POST['pct_icld_adicional_concejo'] or '0')
            if 'categoria_municipio' in request.POST:
                params.categoria_municipio = int(request.POST['categoria_municipio'] or 5)
            params.save()

            # 2. TablaConcejoPersoneria por categoria
            for t in TablaConcejoPersoneria.objects.all():
                pref = f'cat_{t.categoria}_'
                campos_dec = ['valor_sesion_concejal', 'limite_personeria_pct_icld']
                campos_int = ['sesiones_ordinarias', 'sesiones_extraordinarias',
                              'num_concejales', 'personeria_smlv_fijo']
                cambios = []
                for f in campos_dec:
                    if pref + f in request.POST:
                        val = Decimal(request.POST[pref + f] or '0')
                        if getattr(t, f) != val:
                            setattr(t, f, val)
                            cambios.append(f)
                for f in campos_int:
                    if pref + f in request.POST:
                        val = int(request.POST[pref + f] or 0)
                        if getattr(t, f) != val:
                            setattr(t, f, val)
                            cambios.append(f)
                if cambios:
                    t.save(update_fields=cambios)

            # 3. PersoneriaSMLVProgresion
            for p in PersoneriaSMLVProgresion.objects.all():
                key = f'prog_{p.pk}_smlv'
                if key in request.POST:
                    val = int(request.POST[key] or 0)
                    if p.smlv != val:
                        p.smlv = val
                        p.save(update_fields=['smlv'])

            # 4. Recalcular todo
            from ingresos.utils import calcular_todos_ingresos
            from gastos.utils import recalcular_rubros_metodo
            from ingresos.models import RubroIngreso
            from gastos.models import RubroGasto
            calcular_todos_ingresos(params.vigencia)
            recalcular_rubros_metodo(params.vigencia)
            # Propagar titulos
            for t in RubroIngreso.objects.filter(vigencia=params.vigencia, es_titulo=True).order_by('-nivel'):
                t.calcular_hijos()
            for t in RubroGasto.objects.filter(vigencia=params.vigencia, es_titulo=True).order_by('-nivel'):
                t.calcular_hijos()
            messages.success(request, 'Anexo 6 actualizado y rubros recalculados')
        except Exception as e:
            messages.error(request, f'Error al guardar: {e}')
        return redirect('tabla_concejo_personeria')

    icld = Decimal('0')
    valor_smlmv = Decimal('0')
    pct_adic = Decimal('0')
    vigencia_activa = None
    tabla_actual = None
    honorarios = Decimal('0')
    transf_concejo = Decimal('0')
    transf_personeria = Decimal('0')
    smlv_personeria = None
    filas_categoria = []
    progresiones = []

    if params:
        from gastos.utils import calcular_icld
        icld = params.icld_calculado or Decimal('0')
        if icld <= 0:
            icld = calcular_icld(params.vigencia)
        valor_smlmv = params.valor_smlmv or Decimal('0')
        pct_adic = params.pct_icld_adicional_concejo or Decimal('0')
        vigencia_activa = params.vigencia
        adicional_icld = icld * pct_adic  # mismo para todas las categorias

        # Cards de la categoria activa
        tabla_actual = TablaConcejoPersoneria.objects.filter(categoria=params.categoria_municipio).first()
        if tabla_actual:
            honorarios = tabla_actual.calcular_honorarios_concejo(valor_smlmv)
            transf_concejo = tabla_actual.calcular_transferencia_concejo(icld, valor_smlmv, pct_adic)
            transf_personeria = tabla_actual.calcular_transferencia_personeria(vigencia_activa, icld, valor_smlmv)
            prog = PersoneriaSMLVProgresion.objects.filter(
                vigencia=vigencia_activa, categoria=params.categoria_municipio
            ).first()
            if prog:
                smlv_personeria = prog.smlv

        # Tabla integral por categoria con valores calculados
        for t in TablaConcejoPersoneria.objects.all().order_by('categoria'):
            vr_hon = t.calcular_honorarios_concejo(valor_smlmv)
            total_c = vr_hon + adicional_icld

            # SMLV efectivo para esta categoria en la vigencia activa
            prog_cat = PersoneriaSMLVProgresion.objects.filter(
                vigencia=vigencia_activa, categoria=t.categoria).first()
            smlv_efectivo = None
            origen_smlv = ''
            if t.categoria in (0, 1, 2):
                origen_smlv = f'{t.limite_personeria_pct_icld}% ICLD'
            else:
                if prog_cat:
                    smlv_efectivo = prog_cat.smlv
                    origen_smlv = f'{prog_cat.smlv} SMLV (Ley 2461)'
                elif t.personeria_smlv_fijo:
                    smlv_efectivo = t.personeria_smlv_fijo
                    origen_smlv = f'{t.personeria_smlv_fijo} SMLV (fijo)'
                else:
                    origen_smlv = '0'

            total_p = t.calcular_transferencia_personeria(vigencia_activa, icld, valor_smlmv)

            filas_categoria.append({
                'tabla': t,
                'es_actual': t.categoria == params.categoria_municipio,
                'vr_honorarios': vr_hon,
                'adicional_icld': adicional_icld,
                'total_concejo': total_c,
                'smlv_efectivo': smlv_efectivo,
                'origen_smlv': origen_smlv,
                'total_personeria': total_p,
            })

        progresiones = PersoneriaSMLVProgresion.objects.all().order_by('categoria', 'vigencia')

    from .models import CategoriaConcejoChoices
    return render(request, 'core/tabla_concejo.html', {
        'form': form, 'params': params,
        'tabla_actual': tabla_actual,
        'honorarios': honorarios,
        'transf_concejo': transf_concejo,
        'transf_personeria': transf_personeria,
        'icld': icld,
        'smlv_personeria': smlv_personeria,
        'filas_categoria': filas_categoria,
        'vigencia_activa': vigencia_activa,
        'progresiones': progresiones,
        'cat_choices': CategoriaConcejoChoices.choices,
    })


@login_required
def progresion_smlv_guardar(request):
    if request.method == 'POST':
        pk = request.POST.get('pk') or ''
        vigencia = int(request.POST.get('vigencia') or 0)
        categoria = int(request.POST.get('categoria') or 0)
        smlv = int(request.POST.get('smlv') or 0)
        if pk:
            obj = get_object_or_404(PersoneriaSMLVProgresion, pk=pk)
            obj.vigencia = vigencia
            obj.categoria = categoria
            obj.smlv = smlv
            obj.save()
        else:
            PersoneriaSMLVProgresion.objects.update_or_create(
                vigencia=vigencia, categoria=categoria,
                defaults={'smlv': smlv})
        messages.success(request, 'Progresión SMLV guardada')
    return redirect('tabla_concejo_personeria')


@login_required
def progresion_smlv_eliminar(request, pk):
    get_object_or_404(PersoneriaSMLVProgresion, pk=pk).delete()
    messages.success(request, 'Progresión eliminada')
    return redirect('tabla_concejo_personeria')


@never_cache
@login_required
def variables_macro_view(request):
    """Ventana de Variables Macroeconómicas: SMLV, IPC, PIB, etc. por año.

    GET: muestra tabla editable con histórico (2010-2025) y proyecciones (2026+).
    POST: guarda cambios + recalcula todos los rubros que dependen de macro.
    """
    params = ParametrosSistema.objects.filter(activo=True).first()

    if request.method == 'POST':
        # Limpiar puntos de los campos monetarios (SMLV/PIB) que vienen del cop-format
        if hasattr(request.POST, '_mutable'):
            request.POST._mutable = True
            for k in list(request.POST.keys()):
                if k.startswith('var_') and k.endswith('_valor'):
                    request.POST[k] = (request.POST[k] or '').replace('.', '').replace(',', '.')
            request.POST._mutable = False
        try:
            # Guardar cambios de cada variable
            for v in VariableMacro.objects.all():
                key_valor = f'var_{v.pk}_valor'
                key_pct = f'var_{v.pk}_pct'
                cambio = False
                if key_valor in request.POST:
                    nuevo = Decimal(request.POST[key_valor] or '0')
                    if v.valor != nuevo:
                        v.valor = nuevo
                        cambio = True
                if key_pct in request.POST:
                    nuevo = Decimal(request.POST[key_pct] or '0')
                    if v.pct_anual != nuevo:
                        v.pct_anual = nuevo
                        cambio = True
                if cambio:
                    v.save(update_fields=['valor', 'pct_anual'])

            # Sincronizar valor_smlmv y tasa_ipc en ParametrosSistema con el ano vigente
            if params:
                from .models import get_smlv, get_ipc
                smlv_vig = get_smlv(params.vigencia)
                ipc_vig = get_ipc(params.vigencia)
                if smlv_vig:
                    params.valor_smlmv = smlv_vig
                if ipc_vig:
                    params.tasa_ipc = ipc_vig
                params.save(update_fields=['valor_smlmv', 'tasa_ipc'])

                # Recalcular todo
                from ingresos.utils import calcular_todos_ingresos
                from gastos.utils import recalcular_rubros_metodo
                from ingresos.models import RubroIngreso
                from gastos.models import RubroGasto
                calcular_todos_ingresos(params.vigencia)
                recalcular_rubros_metodo(params.vigencia)
                for t in RubroIngreso.objects.filter(vigencia=params.vigencia, es_titulo=True).order_by('-nivel'):
                    t.calcular_hijos()
                for t in RubroGasto.objects.filter(vigencia=params.vigencia, es_titulo=True).order_by('-nivel'):
                    t.calcular_hijos()
            messages.success(request, 'Variables Macro actualizadas y rubros recalculados')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('variables_macro')

    # GET: agrupar por tipo
    TIPOS = ['SMLV', 'IPC', 'PIB', 'PETROLEO', 'DTF', 'TRM']
    grupos = []
    for tipo in TIPOS:
        vars = list(VariableMacro.objects.filter(tipo=tipo).order_by('anio'))
        if vars:
            label = vars[0].get_tipo_display()
            grupos.append({'tipo': tipo, 'label': label, 'variables': vars})

    return render(request, 'core/variables_macro.html', {
        'params': params,
        'grupos': grupos,
        'anios_proyeccion': range(2026, 2037),
    })


@login_required
def variable_macro_agregar(request):
    """Agrega una variable macro nueva."""
    if request.method == 'POST':
        anio = int(request.POST.get('anio') or 0)
        tipo = request.POST.get('tipo')
        valor = Decimal(request.POST.get('valor') or '0')
        pct = Decimal(request.POST.get('pct_anual') or '0')
        es_proy = request.POST.get('es_proyectado') == 'on'
        if anio and tipo:
            VariableMacro.objects.update_or_create(
                anio=anio, tipo=tipo,
                defaults={'valor': valor, 'pct_anual': pct, 'es_proyectado': es_proy})
            messages.success(request, f'Variable {tipo} {anio} agregada')
    return redirect('variables_macro')


@login_required
def variable_macro_eliminar(request, pk):
    get_object_or_404(VariableMacro, pk=pk).delete()
    messages.success(request, 'Variable eliminada')
    return redirect('variables_macro')


@login_required
def tabla_concejo_guardar(request):
    if request.method == 'POST':
        pk = request.POST.get('pk')
        instance = get_object_or_404(TablaConcejoPersoneria, pk=pk) if pk else None
        form = TablaConcejoPersoneriaForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tabla guardada')
    return redirect('tabla_concejo_personeria')


@login_required
def tabla_concejo_eliminar(request, pk):
    get_object_or_404(TablaConcejoPersoneria, pk=pk).delete()
    messages.success(request, 'Registro eliminado')
    return redirect('tabla_concejo_personeria')


def _sincronizar_techos_desde_fuentes(vigencia):
    """Recalcula las columnas Ingresos, Fto y Deuda de cada TechoInversion
    consultando RubroIngreso, RubroGasto y AmortizacionPagare.
    Regla de matching:
      1) Si Techo.codigo_fuente y RubroIngreso.codigo_fuente coinciden → suma.
      2) Adicional: buscar RubroIngreso.nombre que contenga concepto_ingreso (case-insensitive)
         para complementar cuando no hay codigo_fuente.
      3) Deuda: suma servicio_deuda (cap+int) del año vigencia por contratos cuya
         renta_pignorada haga match con el concepto de la fila.
    """
    from decimal import Decimal as D
    from django.db.models import Sum, Q
    try:
        from ingresos.models import RubroIngreso
        from gastos.models import RubroGasto, AmortizacionPagare, ContratoCredito
    except Exception:
        return
    techos = list(TechoInversion.objects.filter(vigencia=vigencia))
    if not techos:
        return

    # Pre-cargar rubros del año
    rubros_ing = list(RubroIngreso.objects.filter(vigencia=vigencia))
    rubros_gto = list(RubroGasto.objects.filter(vigencia=vigencia).exclude(es_titulo=True))

    # Servicio deuda por contrato (año vigencia)
    deuda_por_renta = {}
    for c in ContratoCredito.objects.all():
        agg = AmortizacionPagare.objects.filter(
            pagare__contrato=c, vigencia_pago=vigencia
        ).aggregate(t=Sum('capital_principal'), i=Sum('intereses'))
        val = (agg['t'] or D('0')) + (agg['i'] or D('0'))
        key = (c.renta_pignorada or '').strip().upper()
        if key:
            deuda_por_renta[key] = deuda_por_renta.get(key, D('0')) + val
    deuda_total = sum(deuda_por_renta.values(), D('0'))

    for t in techos:
        concepto_up = (t.concepto_ingreso or '').strip().upper()
        cod = (t.codigo_fuente or '').strip()

        # ── INGRESOS: match por código fuente y por nombre fuzzy
        ingresos_sum = D('0')
        for r in rubros_ing:
            match = False
            if cod and (r.codigo_fuente or '').strip() == cod:
                match = True
            elif concepto_up and concepto_up in (r.descripcion or '').upper():
                match = True
            if match:
                ingresos_sum += (r.valor_apropiacion or D('0'))

        # ── FUNCIONAMIENTO: match por código fuente en gastos de sección 2.1
        fto_sum = D('0')
        for r in rubros_gto:
            if not r.codigo.startswith('2.1'):
                continue
            if cod and (r.codigo_fuente or '').strip() == cod:
                fto_sum += (r.valor_apropiacion or D('0'))

        # ── DEUDA: match por renta pignorada del contrato
        # Reglas: (a) substring exacto; o (b) coinciden >=2 palabras significativas,
        # excluyendo stop-words genericos que aparecen en muchos rubros
        STOP = {'IMPUESTO','RECURSO','RECURSOS','INGRESO','INGRESOS','FONDO','TASA','SGP','DEL','LOS','LAS','POR','PARA','CON','SIN','AL','LA','EL'}
        def _tok(s):
            return {w for w in s.split() if len(w) >= 4 and w not in STOP}
        def _prefijos_comunes(ta, tb, n=5):
            """Cuenta palabras cuyos primeros `n` chars coinciden (soporta plurales/abrev)."""
            count = 0
            pa = {w[:n] for w in ta if len(w) >= n}
            pb = {w[:n] for w in tb if len(w) >= n}
            return len(pa & pb)
        def _match_texto(a, b):
            if not a or not b: return False
            if a in b or b in a: return True
            ta, tb = _tok(a), _tok(b)
            # 2+ prefijos (5 chars) en común
            return _prefijos_comunes(ta, tb, 5) >= 2

        deuda_val = D('0')
        for k, v in deuda_por_renta.items():
            if _match_texto(k, concepto_up):
                deuda_val += v
        # Si no hay match explícito y hay una sola fila con "recursos propios/ITO", la deuda va ahí
        # (skip para no distorsionar)

        dirty = False
        if ingresos_sum > 0 and t.ingresos != ingresos_sum:
            t.ingresos = ingresos_sum; dirty = True
        if fto_sum > 0 and t.fto != fto_sum:
            t.fto = fto_sum; dirty = True
        if t.deuda != deuda_val:
            t.deuda = deuda_val; dirty = True
        if dirty:
            t.save()


@never_cache
@login_required
def techos_inversion_view(request):
    """Reporte Fuentes y Usos: por cada fuente muestra:
    Ingresos + Rendimientos = Total Ingresos
    - Funcionamiento - Deuda = Total Inversion
    - Vigencias Futuras = Disponible
    """
    params = ParametrosSistema.objects.filter(activo=True).first()
    vigencia = params.vigencia if params else 2027

    if request.method == 'POST':
        try:
            # Guardar cambios de las filas existentes
            for t in TechoInversion.objects.filter(vigencia=vigencia):
                pref = f'ti_{t.pk}_'
                cambio = False
                for campo in ['ingresos', 'rendimientos', 'fto', 'deuda', 'vf', 'vivienda', 'medio_ambiente']:
                    k = pref + campo
                    if k in request.POST:
                        raw = request.POST[k] or '0'
                        raw = raw.replace('.', '').replace(',', '.')
                        try:
                            val = Decimal(raw)
                            if getattr(t, campo) != val:
                                setattr(t, campo, val)
                                cambio = True
                        except Exception:
                            pass
                if cambio:
                    t.save()
            messages.success(request, 'Techos de inversion actualizados')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('techos_inversion')

    # Sincronizar desde fuentes antes de mostrar (recursivo)
    try:
        _sincronizar_techos_desde_fuentes(vigencia)
    except Exception:
        pass

    filas = list(TechoInversion.objects.filter(vigencia=vigencia).order_by('orden', 'concepto_ingreso'))
    # Totales
    tot = {
        'ingresos': sum(f.ingresos for f in filas),
        'rendimientos': sum(f.rendimientos for f in filas),
        'fto': sum(f.fto for f in filas),
        'deuda': sum(f.deuda for f in filas),
        'vf': sum(f.vf for f in filas),
        'vivienda': sum(f.vivienda for f in filas),
        'medio_ambiente': sum(f.medio_ambiente for f in filas),
    }
    tot['total_ingresos'] = tot['ingresos'] + tot['rendimientos']
    tot['total_fto_deuda'] = tot['fto'] + tot['deuda']
    tot['total_inversion'] = tot['total_ingresos'] - tot['total_fto_deuda']
    tot['disponible'] = tot['total_inversion'] - tot['vf']

    return render(request, 'core/techos_inversion.html', {
        'filas': filas,
        'totales': tot,
        'vigencia': vigencia,
        'params': params,
    })



# ═══════════════════════════════════════════════════════════════════════════
# MFMP - Vistas del Marco Fiscal de Mediano Plazo (v75)
# ═══════════════════════════════════════════════════════════════════════════

@never_cache
@login_required
def plan_financiero_view(request):
    """Plan Financiero 10 años (A. Ingresos, B. Fto, C. Deuda, D. Inversión)."""
    from .models import PlanFinancieroLinea
    anios = sorted(set(PlanFinancieroLinea.objects.values_list('anio', flat=True)))
    orden = ['A', 'B', 'B1', 'B2', 'C', 'D', 'T']
    filas = []
    for tipo in orden:
        vals = {l.anio: l.valor for l in PlanFinancieroLinea.objects.filter(tipo=tipo)}
        if not vals: continue
        filas.append({
            'tipo': tipo,
            'nombre': dict(PlanFinancieroLinea.TIPO_CHOICES).get(tipo, tipo),
            'valores': [vals.get(a, Decimal('0')) for a in anios],
            'destacado': tipo in ('A', 'T', 'D'),
        })
    return render(request, 'core/plan_financiero.html', {
        'anios': anios, 'filas': filas,
    })


@never_cache
@login_required
def icld_proyectado_view(request):
    """ICLD proyectado 10 años por fuente."""
    from .models import ICLDProyectado, FuenteFinanciacion
    from django.db.models import Sum
    anios = sorted(set(ICLDProyectado.objects.values_list('anio', flat=True)))
    fuentes = FuenteFinanciacion.objects.filter(icld_proyectado__isnull=False).distinct()
    filas = []
    tot_bruto = {a: Decimal('0') for a in anios}
    tot_neto = {a: Decimal('0') for a in anios}
    for f in fuentes:
        proys = {p.anio: p for p in f.icld_proyectado.all()}
        fila = {'fuente': f, 'anios': []}
        for a in anios:
            p = proys.get(a)
            if p:
                bruto = p.valor_bruto or Decimal('0')
                neto = p.icld_neto or Decimal('0')
                tot_bruto[a] += bruto
                tot_neto[a] += neto
                fila['anios'].append({'bruto': bruto, 'neto': neto})
            else:
                fila['anios'].append({'bruto': Decimal('0'), 'neto': Decimal('0')})
        filas.append(fila)
    pares_totales = [{'bruto': tot_bruto[a], 'neto': tot_neto[a]} for a in anios]
    return render(request, 'core/icld_proyectado.html', {
        'anios': anios, 'filas': filas,
        'pares_totales': pares_totales,
    })


@never_cache
@login_required
def ley_617_view(request):
    """Ley 617/2000 proyectada: GF vs ICLD Neto + semáforo cumplimiento."""
    from .models import Ley617Proyectado
    filas = list(Ley617Proyectado.objects.all().order_by('anio'))
    return render(request, 'core/ley_617_proyectado.html', {'filas': filas})


@never_cache
@login_required
def poai_proyectado_view(request):
    """POAI 10 años por fuente + totales."""
    from .models import POAIProyectado, FuenteFinanciacion
    from django.db.models import Sum
    anios = sorted(set(POAIProyectado.objects.values_list('anio', flat=True)))
    fuentes = list(FuenteFinanciacion.objects.filter(poai_proyectado__isnull=False).distinct())
    filas = []
    tot = {a: Decimal('0') for a in anios}
    for f in fuentes:
        proys = {p.anio: p.valor for p in f.poai_proyectado.all()}
        vals = [proys.get(a, Decimal('0')) for a in anios]
        for i, a in enumerate(anios):
            tot[a] += vals[i]
        filas.append({'fuente': f, 'valores': vals, 'total_10y': sum(vals)})
    filas.sort(key=lambda x: -x['total_10y'])
    return render(request, 'core/poai_proyectado.html', {
        'anios': anios, 'filas': filas,
        'totales': [tot[a] for a in anios],
    })


@never_cache
@login_required
def poai_dependencias_view(request):
    """POAI por dependencia con % participación."""
    from .models import POAIPorDependencia
    from django.db.models import Sum
    anios = sorted(set(POAIPorDependencia.objects.values_list('anio', flat=True)))
    deps = POAIPorDependencia.objects.values('dependencia', 'pct_participacion').distinct()
    filas = []
    tot = {a: Decimal('0') for a in anios}
    for d in deps:
        proys = {p.anio: p.valor for p in POAIPorDependencia.objects.filter(dependencia=d['dependencia'])}
        vals = [proys.get(a, Decimal('0')) for a in anios]
        for i, a in enumerate(anios):
            tot[a] += vals[i]
        filas.append({
            'dependencia': d['dependencia'],
            'pct': d['pct_participacion'],
            'valores': vals,
            'total_10y': sum(vals),
        })
    filas.sort(key=lambda x: -x['pct'])
    return render(request, 'core/poai_dependencias.html', {
        'anios': anios, 'filas': filas,
        'totales': [tot[a] for a in anios],
    })


@never_cache
@login_required
def cuadre_fuente_view(request):
    """Cuadre Ingreso vs Gasto por fuente (validador)."""
    from .models import CuadrePorFuente, FuenteFinanciacion
    anios = sorted(set(CuadrePorFuente.objects.values_list('anio', flat=True)), reverse=True)
    fuentes = FuenteFinanciacion.objects.filter(cuadres__isnull=False).distinct()
    filas = []
    for f in fuentes:
        cuadres = {c.anio: c for c in f.cuadres.all()}
        fila = {'fuente': f, 'anios': []}
        for a in anios:
            c = cuadres.get(a)
            if c:
                fila['anios'].append({
                    'ingreso': c.ingreso, 'gasto': c.gasto,
                    'dif': c.diferencia, 'cuadra': c.cuadra,
                })
            else:
                fila['anios'].append({'ingreso': 0, 'gasto': 0, 'dif': 0, 'cuadra': True})
        filas.append(fila)
    filas.sort(key=lambda x: (all(v['cuadra'] for v in x['anios']),
                              -sum((v['ingreso'] or 0) for v in x['anios'])))
    return render(request, 'core/cuadre_fuente.html', {'anios': anios, 'filas': filas})


@never_cache
@login_required
def saldo_vf_fuente_view(request):
    """Saldo VF disponible por fuente."""
    from .models import SaldoVFPorFuente
    filas = list(SaldoVFPorFuente.objects.select_related('fuente').all().order_by('fuente__codigo'))
    from django.db.models import Sum
    tot = SaldoVFPorFuente.objects.aggregate(
        ap=Sum('apropiacion_definitiva'),
        va=Sum('vf_aprobadas'),
        vt=Sum('vf_en_tramite'),
    )
    return render(request, 'core/saldo_vf_fuente.html', {
        'filas': filas, 'total': tot,
    })


@never_cache
@login_required
def mfmp_menu(request):
    """Menú principal del MFMP."""
    from .models import (PlanFinancieroLinea, ICLDProyectado, Ley617Proyectado,
                         POAIProyectado, POAIPorDependencia, CuadrePorFuente,
                         SaldoVFPorFuente)
    stats = {
        'plan_financiero': PlanFinancieroLinea.objects.count(),
        'icld': ICLDProyectado.objects.count(),
        'ley_617': Ley617Proyectado.objects.count(),
        'poai': POAIProyectado.objects.count(),
        'poai_dep': POAIPorDependencia.objects.count(),
        'cuadre': CuadrePorFuente.objects.count(),
        'saldo_vf': SaldoVFPorFuente.objects.count(),
    }
    return render(request, 'core/mfmp_menu.html', {'stats': stats})
