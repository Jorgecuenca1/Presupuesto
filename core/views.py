from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from .forms import LoginForm, RegistroForm, ParametrosForm
from .models import ParametrosSistema


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
    params = ParametrosSistema.objects.filter(activo=True).first()
    vigencia = params.vigencia if params else 2026

    total_contribuyentes_predial = ContribuyentePredial.objects.filter(vigencia=vigencia).count()
    total_contribuyentes_ica = ContribuyenteICA.objects.filter(vigencia=vigencia).count()
    total_ingresos = RubroIngreso.objects.filter(
        vigencia=vigencia, es_titulo=False
    ).aggregate(total=Sum('valor_apropiacion'))['total'] or 0

    rubros_por_metodo = RubroIngreso.objects.filter(
        vigencia=vigencia, es_titulo=False
    ).exclude(metodo_calculo='MAN').values('metodo_calculo').annotate(
        total=Sum('valor_apropiacion'), cantidad=Count('id')
    ).order_by('-total')

    context = {
        'params': params,
        'total_contribuyentes_predial': total_contribuyentes_predial,
        'total_contribuyentes_ica': total_contribuyentes_ica,
        'total_ingresos': total_ingresos,
        'rubros_por_metodo': rubros_por_metodo,
    }
    return render(request, 'core/dashboard.html', context)


@login_required
def parametros_view(request):
    params = ParametrosSistema.objects.filter(activo=True).first()
    if request.method == 'POST':
        form = ParametrosForm(request.POST, instance=params)
        if form.is_valid():
            form.save()
            messages.success(request, 'Parámetros guardados correctamente')
            return redirect('parametros')
    else:
        form = ParametrosForm(instance=params)
    return render(request, 'ingresos/parametros_form.html', {'form': form, 'params': params})
