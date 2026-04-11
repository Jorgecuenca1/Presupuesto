from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from decimal import Decimal
from .forms import LoginForm, RegistroForm, ParametrosForm, TablaConcejoPersoneriaForm
from .models import ParametrosSistema, TablaConcejoPersoneria


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
    from ingresos.models import ContribuyentePredial, ContribuyenteICA, RubroIngreso
    from gastos.models import RubroGasto
    params = ParametrosSistema.objects.filter(activo=True).first()
    vigencia = params.vigencia if params else 2026

    total_contribuyentes_predial = ContribuyentePredial.objects.filter(vigencia=vigencia).count()
    total_contribuyentes_ica = ContribuyenteICA.objects.filter(vigencia=vigencia).count()

    # Total ingresos - buscar primero en títulos nivel 0, si no en rubros hoja
    total_ingresos_titulo = RubroIngreso.objects.filter(
        vigencia=vigencia, nivel=0, es_titulo=True
    ).aggregate(total=Sum('valor_apropiacion'))['total']
    if not total_ingresos_titulo:
        total_ingresos_titulo = RubroIngreso.objects.filter(
            vigencia=vigencia, es_titulo=False
        ).aggregate(total=Sum('valor_apropiacion'))['total'] or 0
    total_ingresos = total_ingresos_titulo

    # Total gastos
    total_gastos_titulo = RubroGasto.objects.filter(
        vigencia=vigencia, nivel=0, es_titulo=True
    ).aggregate(total=Sum('valor_apropiacion'))['total']
    if not total_gastos_titulo:
        total_gastos_titulo = RubroGasto.objects.filter(
            vigencia=vigencia, es_titulo=False
        ).aggregate(total=Sum('valor_apropiacion'))['total'] or 0
    total_gastos = total_gastos_titulo

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
            try:
                calcular_todos_ingresos(params_saved.vigencia)
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
    tablas = TablaConcejoPersoneria.objects.all()
    form = TablaConcejoPersoneriaForm()

    params = ParametrosSistema.objects.filter(activo=True).first()
    tabla_actual = None
    honorarios = Decimal('0')
    limite_concejo = Decimal('0')
    limite_personeria = Decimal('0')
    if params:
        tabla_actual = TablaConcejoPersoneria.objects.filter(categoria=params.categoria_municipio).first()
        if tabla_actual and params.valor_smlmv > 0:
            honorarios = tabla_actual.calcular_honorarios_concejo(params.valor_smlmv)

    return render(request, 'core/tabla_concejo.html', {
        'tablas': tablas, 'form': form, 'params': params,
        'tabla_actual': tabla_actual,
        'honorarios': honorarios,
    })


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
