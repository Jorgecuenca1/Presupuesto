from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from decimal import Decimal
from .forms import LoginForm, RegistroForm, ParametrosForm, TablaConcejoPersoneriaForm
from .models import ParametrosSistema, TablaConcejoPersoneria, PersoneriaSMLVProgresion


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
    total_predial = ResumenCalculo.objects.filter(
        vigencia=vigencia, tipo__in=['predial_urbano', 'predial_rural']
    ).aggregate(t=Sum('proyeccion'))['t'] or Decimal('0')
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
    }
    return render(request, 'core/dashboard.html', context)


@login_required
def parametros_view(request):
    params = ParametrosSistema.objects.filter(activo=True).first()
    if not params:
        params = ParametrosSistema.objects.order_by('-vigencia').first()

    # Autollenar ICLD si esta en 0 y hay cifras historicas
    if params and (params.icld_calculado is None or params.icld_calculado == 0):
        from gastos.utils import calcular_icld
        icld_auto = calcular_icld(params.vigencia)
        if icld_auto > 0:
            params.icld_calculado = icld_auto

    if request.method == 'POST':
        form = ParametrosForm(request.POST, instance=params)
        if form.is_valid():
            params_saved = form.save(commit=False)
            params_saved.activo = True
            params_saved.save()

            # Recalcular ingresos y gastos con los nuevos parámetros
            from ingresos.utils import calcular_todos_ingresos
            from ingresos.models import RubroIngreso
            from gastos.models import RubroGasto
            from gastos.utils import recalcular_rubros_metodo
            try:
                calcular_todos_ingresos(params_saved.vigencia)
                recalcular_rubros_metodo(params_saved.vigencia)
                titulos_ing = RubroIngreso.objects.filter(
                    vigencia=params_saved.vigencia, es_titulo=True
                ).order_by('-nivel')
                for t in titulos_ing:
                    t.calcular_hijos()
                titulos_gas = RubroGasto.objects.filter(
                    vigencia=params_saved.vigencia, es_titulo=True
                ).order_by('-nivel')
                for t in titulos_gas:
                    t.calcular_hijos()
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


@login_required
def tabla_concejo_personeria(request):
    """Anexo 6 - Organos de Control.

    Muestra una tabla integral por categoria municipal con valores calculados:
    - Vr Honorarios = valor_sesion x (ord+extra) x concejales
    - %ICLD Adicional = ICLD x pct_icld_adicional_concejo
    - Total Concejo  = Vr Honorarios + %ICLD Adicional
    - SMLV efectivo  = de la progresion vigente (o smlv_fijo si no hay progresion)
    - Total Personeria segun categoria (ICLD%, SMLV fijo, o SMLV progresion).
    """
    form = TablaConcejoPersoneriaForm()
    params = ParametrosSistema.objects.filter(activo=True).first()

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
