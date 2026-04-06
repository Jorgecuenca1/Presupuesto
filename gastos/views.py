from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.http import HttpResponse
from decimal import Decimal, InvalidOperation
import openpyxl

from core.models import ParametrosSistema
from .models import RubroGasto, SeccionGasto, FuenteFinanciacion, EjecucionGasto, TipoGasto
from .forms import (
    RubroGastoForm, SeccionGastoForm, FuenteFinanciacionForm,
    EjecucionGastoForm, ImportarGastosExcelForm,
)


def _vigencia():
    p = ParametrosSistema.objects.filter(activo=True).first()
    return p.vigencia if p else 2026


def _safe_decimal(val):
    if val is None:
        return Decimal('0')
    try:
        return Decimal(str(val).replace(',', '').replace('$', '').strip())
    except (InvalidOperation, ValueError, TypeError):
        return Decimal('0')


# ─── SECCIONES ────────────────────────────────────────────────────
@login_required
def secciones_list(request):
    vigencia = _vigencia()
    secciones = SeccionGasto.objects.filter(vigencia=vigencia)
    form = SeccionGastoForm(initial={'vigencia': vigencia})
    return render(request, 'gastos/secciones_list.html', {
        'secciones': secciones, 'form': form, 'vigencia': vigencia,
    })


@login_required
def seccion_guardar(request):
    if request.method == 'POST':
        pk = request.POST.get('pk')
        instance = get_object_or_404(SeccionGasto, pk=pk) if pk else None
        form = SeccionGastoForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sección guardada')
    return redirect('gastos_secciones')


@login_required
def seccion_eliminar(request, pk):
    get_object_or_404(SeccionGasto, pk=pk).delete()
    messages.success(request, 'Sección eliminada')
    return redirect('gastos_secciones')


# ─── FUENTES ──────────────────────────────────────────────────────
@login_required
def fuentes_list(request):
    vigencia = _vigencia()
    fuentes = FuenteFinanciacion.objects.filter(vigencia=vigencia)
    form = FuenteFinanciacionForm(initial={'vigencia': vigencia})
    return render(request, 'gastos/fuentes_list.html', {
        'fuentes': fuentes, 'form': form, 'vigencia': vigencia,
    })


@login_required
def fuente_guardar(request):
    if request.method == 'POST':
        pk = request.POST.get('pk')
        instance = get_object_or_404(FuenteFinanciacion, pk=pk) if pk else None
        form = FuenteFinanciacionForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fuente guardada')
    return redirect('gastos_fuentes')


@login_required
def fuente_eliminar(request, pk):
    get_object_or_404(FuenteFinanciacion, pk=pk).delete()
    messages.success(request, 'Fuente eliminada')
    return redirect('gastos_fuentes')


# ─── RUBROS DE GASTO ─────────────────────────────────────────────
@login_required
def rubros_gasto_list(request):
    vigencia = _vigencia()
    rubros = RubroGasto.objects.filter(vigencia=vigencia)
    total = rubros.filter(es_titulo=False).aggregate(t=Sum('valor_apropiacion'))['t'] or 0
    return render(request, 'gastos/rubros_gasto_list.html', {
        'rubros': rubros, 'vigencia': vigencia, 'total': total,
    })


@login_required
def rubro_gasto_crear(request):
    vigencia = _vigencia()
    if request.method == 'POST':
        form = RubroGastoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rubro de gasto creado')
            return redirect('rubros_gasto_list')
    else:
        form = RubroGastoForm(initial={'vigencia': vigencia})
    return render(request, 'gastos/rubro_gasto_form.html', {'form': form, 'titulo': 'Crear Rubro de Gasto'})


@login_required
def rubro_gasto_editar(request, pk):
    rubro = get_object_or_404(RubroGasto, pk=pk)
    if request.method == 'POST':
        form = RubroGastoForm(request.POST, instance=rubro)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rubro actualizado')
            return redirect('rubros_gasto_list')
    else:
        form = RubroGastoForm(instance=rubro)
    return render(request, 'gastos/rubro_gasto_form.html', {'form': form, 'titulo': 'Editar Rubro de Gasto'})


@login_required
def rubro_gasto_eliminar(request, pk):
    get_object_or_404(RubroGasto, pk=pk).delete()
    messages.success(request, 'Rubro eliminado')
    return redirect('rubros_gasto_list')


# ─── RECALCULAR TÍTULOS ──────────────────────────────────────────
@login_required
def recalcular_gastos(request):
    vigencia = _vigencia()
    if request.method == 'POST':
        titulos = RubroGasto.objects.filter(vigencia=vigencia, es_titulo=True).order_by('-nivel')
        for titulo in titulos:
            titulo.calcular_hijos()
        messages.success(request, 'Rubros de gasto recalculados correctamente')
    return redirect('reporte_gastos')


# ─── IMPORTAR ANEXO 2 (PRESUPUESTO DE GASTOS) ────────────────────
@login_required
def importar_anexo2(request):
    if request.method == 'POST':
        form = ImportarGastosExcelForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = request.FILES['archivo']
            vigencia = _vigencia()
            try:
                wb = openpyxl.load_workbook(archivo, data_only=True)
                # Buscar la hoja principal
                sheet_name = None
                for name in wb.sheetnames:
                    if 'ANEXO' in name.upper() or 'DETALLE' in name.upper() or 'GASTO' in name.upper():
                        sheet_name = name
                        break
                if not sheet_name:
                    sheet_name = wb.sheetnames[0]
                ws = wb[sheet_name]

                # Detectar columnas por encabezados
                header_row = None
                col_map = {}
                for row_idx, row in enumerate(ws.iter_rows(min_row=1, max_row=15, values_only=False), 1):
                    for cell in row:
                        val = str(cell.value or '').upper().strip()
                        if 'SECCION' in val and 'NOMBRE' not in val and 'INVERSION' not in val:
                            col_map['seccion'] = cell.column - 1
                            header_row = row_idx
                        elif 'NOMBRE' in val and 'SECCION' in val:
                            col_map['nombre_seccion'] = cell.column - 1
                        elif 'IDENTIFICACION' in val or 'IDENTIFICACIÓN' in val:
                            col_map['codigo'] = cell.column - 1
                        elif val == 'FUENTE' or 'COD' in val and 'FTE' in val:
                            if 'cod_fuente' not in col_map:
                                col_map['cod_fuente'] = cell.column - 1
                        elif 'NOMBRE' in val and 'FUENTE' in val:
                            col_map['nombre_fuente'] = cell.column - 1
                        elif 'DESCRIPCION' in val or 'DESCRIPCIÓN' in val:
                            col_map['descripcion'] = cell.column - 1
                        elif 'APROPIACION' in val or 'APROPIACIÓN' in val:
                            col_map['apropiacion'] = cell.column - 1
                    if header_row:
                        break

                if not header_row or 'codigo' not in col_map:
                    messages.error(request, 'No se pudo detectar la estructura del archivo. Verifique que tenga columnas de IDENTIFICACIÓN PRESUPUESTAL y APROPIACIÓN.')
                    return redirect('importar_anexo2')

                # Borrar rubros existentes de esta vigencia antes de importar
                RubroGasto.objects.filter(vigencia=vigencia).delete()
                SeccionGasto.objects.filter(vigencia=vigencia).delete()
                FuenteFinanciacion.objects.filter(vigencia=vigencia).delete()

                count = 0
                orden = 0
                seccion_cache = {}
                fuente_cache = {}
                parent_stack = {}  # nivel -> último rubro título de ese nivel

                for row in ws.iter_rows(min_row=header_row + 1, values_only=True):
                    codigo_raw = str(row[col_map['codigo']] or '').strip() if 'codigo' in col_map and row[col_map['codigo']] else ''
                    descripcion = str(row[col_map.get('descripcion', col_map.get('codigo', 0))] or '').strip() if col_map.get('descripcion') is not None and len(row) > col_map.get('descripcion', 0) else ''

                    if not codigo_raw and not descripcion:
                        continue
                    if not codigo_raw:
                        continue

                    # Obtener sección
                    seccion_cod = str(row[col_map['seccion']] or '').strip() if 'seccion' in col_map and len(row) > col_map.get('seccion', 0) else ''
                    seccion_nombre = str(row[col_map['nombre_seccion']] or '').strip() if 'nombre_seccion' in col_map and len(row) > col_map.get('nombre_seccion', 0) else ''
                    seccion_obj = None
                    if seccion_cod:
                        if seccion_cod not in seccion_cache:
                            seccion_obj, _ = SeccionGasto.objects.get_or_create(
                                vigencia=vigencia, codigo=seccion_cod,
                                defaults={'nombre': seccion_nombre or seccion_cod}
                            )
                            seccion_cache[seccion_cod] = seccion_obj
                        else:
                            seccion_obj = seccion_cache[seccion_cod]

                    # Obtener fuente
                    cod_fuente = str(row[col_map['cod_fuente']] or '').strip() if 'cod_fuente' in col_map and len(row) > col_map.get('cod_fuente', 0) else ''
                    nombre_fuente = str(row[col_map['nombre_fuente']] or '').strip() if 'nombre_fuente' in col_map and len(row) > col_map.get('nombre_fuente', 0) else ''
                    fuente_obj = None
                    if cod_fuente:
                        if cod_fuente not in fuente_cache:
                            fuente_obj, _ = FuenteFinanciacion.objects.get_or_create(
                                vigencia=vigencia, codigo=cod_fuente,
                                defaults={'nombre': nombre_fuente or cod_fuente}
                            )
                            fuente_cache[cod_fuente] = fuente_obj
                        else:
                            fuente_obj = fuente_cache[cod_fuente]

                    # Apropiación
                    val_aprop = Decimal('0')
                    if 'apropiacion' in col_map and len(row) > col_map['apropiacion']:
                        val_aprop = _safe_decimal(row[col_map['apropiacion']])

                    # Determinar nivel jerárquico por el código
                    parts = codigo_raw.replace('-', '.').split('.')
                    nivel = len(parts) - 1
                    es_titulo = nivel < 3 and val_aprop == 0  # Los niveles altos sin valor son títulos

                    # Si tiene hijos potenciales (pocos segmentos), es título
                    if nivel <= 2:
                        es_titulo = True

                    # Determinar tipo de gasto
                    tipo_gasto = 'FUN'
                    desc_upper = descripcion.upper()
                    if 'INVERSIÓN' in desc_upper or 'INVERSION' in desc_upper:
                        tipo_gasto = 'INV'
                    elif 'DEUDA' in desc_upper:
                        tipo_gasto = 'DEU'

                    # Buscar parent
                    parent = None
                    if nivel > 0:
                        parent = parent_stack.get(nivel - 1)

                    orden += 1
                    rubro = RubroGasto.objects.create(
                        vigencia=vigencia,
                        codigo=codigo_raw,
                        descripcion=descripcion,
                        seccion=seccion_obj,
                        fuente=fuente_obj,
                        codigo_fuente=cod_fuente,
                        nombre_fuente=nombre_fuente,
                        tipo_gasto=tipo_gasto,
                        parent=parent,
                        valor_apropiacion=val_aprop if not es_titulo else 0,
                        es_titulo=es_titulo,
                        orden=orden,
                        nivel=nivel,
                    )

                    if es_titulo:
                        parent_stack[nivel] = rubro

                    count += 1

                # Recalcular títulos de abajo hacia arriba
                titulos = RubroGasto.objects.filter(vigencia=vigencia, es_titulo=True).order_by('-nivel')
                for titulo in titulos:
                    titulo.calcular_hijos()

                messages.success(request, f'{count} rubros de gasto importados desde Anexo 2')
                return redirect('rubros_gasto_list')
            except Exception as e:
                messages.error(request, f'Error al importar: {e}')
    else:
        form = ImportarGastosExcelForm()
    return render(request, 'gastos/importar_gastos.html', {
        'form': form,
        'tipo': 'Anexo 2 - Presupuesto de Gastos',
        'descripcion': 'Importe el archivo Excel del Anexo 2 (Presupuesto de Gastos Central). El sistema detectará automáticamente las columnas: Sección, Identificación Presupuestal, Fuente, Descripción y Apropiación.',
    })


# ─── IMPORTAR EJECUCIÓN DE GASTOS ─────────────────────────────────
@login_required
def importar_ejecucion(request):
    if request.method == 'POST':
        form = ImportarGastosExcelForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = request.FILES['archivo']
            vigencia = _vigencia()
            try:
                wb = openpyxl.load_workbook(archivo, data_only=True)
                # Buscar la hoja de gastos
                sheet_name = None
                for name in wb.sheetnames:
                    if 'GASTO' in name.upper():
                        sheet_name = name
                        break
                if not sheet_name:
                    sheet_name = wb.sheetnames[0]
                ws = wb[sheet_name]

                # Detectar columnas por encabezados
                header_row = None
                col_map = {}
                for row_idx, row in enumerate(ws.iter_rows(min_row=1, max_row=10, values_only=False), 1):
                    for cell in row:
                        val = str(cell.value or '').upper().strip()
                        if 'RUBRO' in val and 'PPTAL' in val:
                            col_map['codigo'] = cell.column - 1
                            header_row = row_idx
                        elif 'DESCRIPCI' in val and 'RUBRO' in val:
                            col_map['descripcion'] = cell.column - 1
                        elif 'PRESUPUESTO' in val and 'APROBADO' in val:
                            col_map['aprobado'] = cell.column - 1
                        elif val == 'ADICIONES':
                            col_map['adiciones'] = cell.column - 1
                        elif val == 'REDUCCIONES':
                            col_map['reducciones'] = cell.column - 1
                        elif 'TRASLADO' in val and 'CREDITO' in val and 'CONTRA' not in val:
                            col_map['traslado_credito'] = cell.column - 1
                        elif 'CONTRA' in val and ('CREDITO' in val or 'CRÉDITO' in val):
                            col_map['traslado_contra'] = cell.column - 1
                        elif 'APLAZAMIENTO' in val and 'DES' not in val:
                            col_map['aplazamientos'] = cell.column - 1
                        elif 'DESAPLAZAMIENTO' in val:
                            col_map['desaplazamientos'] = cell.column - 1
                        elif val == 'CDP' or 'CDP' in val and 'SALDO' not in val and 'COMPROMETER' not in val:
                            if 'cdp' not in col_map:
                                col_map['cdp'] = cell.column - 1
                        elif 'COMPROMISO' in val:
                            col_map['compromisos'] = cell.column - 1
                        elif 'ORDENADO' in val or 'OBLIGACION' in val:
                            col_map['ordenado'] = cell.column - 1
                        elif 'PAGADO' in val or 'PAGO' in val:
                            col_map['pagado'] = cell.column - 1
                        elif 'FUENTE' in val and 'PPTAL' in val and 'DESCRIPCI' not in val:
                            col_map['fuente'] = cell.column - 1
                        elif 'DESCRIPCI' in val and 'FUENTE' in val:
                            col_map['nombre_fuente'] = cell.column - 1
                        elif 'TIPO' in val and 'GASTO' in val:
                            col_map['tipo_gasto'] = cell.column - 1
                    if header_row:
                        break

                if not header_row or 'codigo' not in col_map:
                    messages.error(request, 'No se pudo detectar la estructura del archivo de ejecución.')
                    return redirect('importar_ejecucion')

                count_new = 0
                count_updated = 0

                for row in ws.iter_rows(min_row=header_row + 1, values_only=True):
                    codigo = str(row[col_map['codigo']] or '').strip() if len(row) > col_map['codigo'] else ''
                    if not codigo:
                        continue

                    descripcion = ''
                    if 'descripcion' in col_map and len(row) > col_map['descripcion']:
                        descripcion = str(row[col_map['descripcion']] or '').strip()

                    # Buscar rubro existente o crear nuevo
                    rubro = RubroGasto.objects.filter(vigencia=vigencia, codigo=codigo).first()
                    if not rubro:
                        parts = codigo.replace('-', '.').split('.')
                        nivel = len(parts) - 1
                        rubro = RubroGasto.objects.create(
                            vigencia=vigencia,
                            codigo=codigo,
                            descripcion=descripcion,
                            nivel=nivel,
                            es_titulo=False,
                            orden=RubroGasto.objects.filter(vigencia=vigencia).count() + 1,
                        )
                        count_new += 1

                    # Crear o actualizar ejecución
                    ej, created = EjecucionGasto.objects.get_or_create(rubro=rubro)
                    ej.presupuesto_aprobado = _safe_decimal(row[col_map['aprobado']]) if 'aprobado' in col_map and len(row) > col_map['aprobado'] else ej.presupuesto_aprobado
                    ej.adiciones = _safe_decimal(row[col_map['adiciones']]) if 'adiciones' in col_map and len(row) > col_map['adiciones'] else ej.adiciones
                    ej.reducciones = _safe_decimal(row[col_map['reducciones']]) if 'reducciones' in col_map and len(row) > col_map['reducciones'] else ej.reducciones
                    ej.traslado_credito = _safe_decimal(row[col_map['traslado_credito']]) if 'traslado_credito' in col_map and len(row) > col_map['traslado_credito'] else ej.traslado_credito
                    ej.traslado_contra_credito = _safe_decimal(row[col_map['traslado_contra']]) if 'traslado_contra' in col_map and len(row) > col_map['traslado_contra'] else ej.traslado_contra_credito
                    ej.aplazamientos = _safe_decimal(row[col_map['aplazamientos']]) if 'aplazamientos' in col_map and len(row) > col_map['aplazamientos'] else ej.aplazamientos
                    ej.desaplazamientos = _safe_decimal(row[col_map['desaplazamientos']]) if 'desaplazamientos' in col_map and len(row) > col_map['desaplazamientos'] else ej.desaplazamientos
                    ej.cdp = _safe_decimal(row[col_map['cdp']]) if 'cdp' in col_map and len(row) > col_map['cdp'] else ej.cdp
                    ej.compromisos = _safe_decimal(row[col_map['compromisos']]) if 'compromisos' in col_map and len(row) > col_map['compromisos'] else ej.compromisos
                    ej.ordenado = _safe_decimal(row[col_map['ordenado']]) if 'ordenado' in col_map and len(row) > col_map['ordenado'] else ej.ordenado
                    ej.pagado = _safe_decimal(row[col_map['pagado']]) if 'pagado' in col_map and len(row) > col_map['pagado'] else ej.pagado
                    ej.save()
                    count_updated += 1

                messages.success(request, f'Ejecución importada: {count_updated} registros actualizados, {count_new} rubros nuevos creados')
                return redirect('ejecucion_gastos')
            except Exception as e:
                messages.error(request, f'Error al importar ejecución: {e}')
    else:
        form = ImportarGastosExcelForm()
    return render(request, 'gastos/importar_gastos.html', {
        'form': form,
        'tipo': 'Ejecución de Gastos',
        'descripcion': 'Importe el archivo Excel de Ejecución de Gastos. El sistema detectará automáticamente las columnas: Rubro, Presupuesto Aprobado, Adiciones, Reducciones, CDP, Compromisos, Ordenado y Pagado.',
    })


# ─── EJECUCIÓN DE GASTOS ─────────────────────────────────────────
@login_required
def ejecucion_gastos(request):
    vigencia = _vigencia()
    rubros_con_ejecucion = RubroGasto.objects.filter(
        vigencia=vigencia, es_titulo=False, ejecucion__isnull=False
    ).select_related('ejecucion', 'seccion')

    totales = EjecucionGasto.objects.filter(rubro__vigencia=vigencia).aggregate(
        total_aprobado=Sum('presupuesto_aprobado'),
        total_adiciones=Sum('adiciones'),
        total_reducciones=Sum('reducciones'),
        total_cdp=Sum('cdp'),
        total_compromisos=Sum('compromisos'),
        total_ordenado=Sum('ordenado'),
        total_pagado=Sum('pagado'),
    )

    total_aprobado = totales['total_aprobado'] or 0
    total_compromisos = totales['total_compromisos'] or 0
    pct_ejecucion = (Decimal(str(total_compromisos)) / Decimal(str(total_aprobado)) * 100).quantize(Decimal('0.01')) if total_aprobado else Decimal('0')

    return render(request, 'gastos/ejecucion_gastos.html', {
        'rubros': rubros_con_ejecucion,
        'vigencia': vigencia,
        'totales': totales,
        'pct_ejecucion': pct_ejecucion,
    })


# ─── EDITAR EJECUCIÓN INDIVIDUAL ──────────────────────────────────
@login_required
def ejecucion_editar(request, pk):
    rubro = get_object_or_404(RubroGasto, pk=pk)
    ejecucion, created = EjecucionGasto.objects.get_or_create(rubro=rubro)
    if request.method == 'POST':
        form = EjecucionGastoForm(request.POST, instance=ejecucion)
        if form.is_valid():
            form.save()
            messages.success(request, f'Ejecución de {rubro.codigo} actualizada')
            return redirect('ejecucion_gastos')
    else:
        form = EjecucionGastoForm(instance=ejecucion)
    return render(request, 'gastos/ejecucion_form.html', {
        'form': form, 'rubro': rubro,
    })


# ─── REPORTE ANEXO 2 ─────────────────────────────────────────────
@login_required
def reporte_gastos(request):
    vigencia = _vigencia()
    params = ParametrosSistema.objects.filter(vigencia=vigencia).first()
    rubros = RubroGasto.objects.filter(vigencia=vigencia)
    total = rubros.filter(nivel=0, es_titulo=True).aggregate(t=Sum('valor_apropiacion'))['t']
    if not total:
        total = rubros.filter(es_titulo=False).aggregate(t=Sum('valor_apropiacion'))['t'] or 0

    # Totales por tipo de gasto
    total_funcionamiento = rubros.filter(tipo_gasto='FUN', es_titulo=False).aggregate(t=Sum('valor_apropiacion'))['t'] or 0
    total_inversion = rubros.filter(tipo_gasto='INV', es_titulo=False).aggregate(t=Sum('valor_apropiacion'))['t'] or 0
    total_deuda = rubros.filter(tipo_gasto='DEU', es_titulo=False).aggregate(t=Sum('valor_apropiacion'))['t'] or 0

    return render(request, 'gastos/reporte_gastos.html', {
        'rubros': rubros, 'vigencia': vigencia, 'params': params, 'total': total,
        'total_funcionamiento': total_funcionamiento,
        'total_inversion': total_inversion,
        'total_deuda': total_deuda,
    })


# ─── EXPORTAR EXCEL ──────────────────────────────────────────────
@login_required
def exportar_gastos_excel(request):
    vigencia = _vigencia()
    rubros = RubroGasto.objects.filter(vigencia=vigencia)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Anexo 2 Detalle Gastos'
    ws.append(['MUNICIPIO DE PUERTO LÓPEZ'])
    ws.append(['PRESUPUESTO DE GASTOS - ADMINISTRACIÓN CENTRAL'])
    ws.append([f'VIGENCIA FISCAL {vigencia}'])
    ws.append([])
    ws.append(['SECCIÓN', 'IDENTIFICACIÓN', 'COD FUENTE', 'FUENTE', 'DESCRIPCIÓN', 'APROPIACIÓN', 'OBSERVACIONES'])

    for rubro in rubros:
        indent = '  ' * rubro.nivel
        ws.append([
            rubro.seccion.codigo if rubro.seccion else '',
            rubro.codigo,
            rubro.codigo_fuente,
            rubro.nombre_fuente,
            indent + rubro.descripcion,
            float(rubro.valor_apropiacion),
            rubro.observaciones,
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=Anexo2_Gastos_{vigencia}.xlsx'
    wb.save(response)
    return response


# ─── EXPORTAR EJECUCIÓN EXCEL ────────────────────────────────────
@login_required
def exportar_ejecucion_excel(request):
    vigencia = _vigencia()
    rubros = RubroGasto.objects.filter(
        vigencia=vigencia, es_titulo=False, ejecucion__isnull=False
    ).select_related('ejecucion')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Ejecución Gastos'
    ws.append(['MUNICIPIO DE PUERTO LÓPEZ'])
    ws.append([f'EJECUCIÓN PRESUPUESTAL DE GASTOS - VIGENCIA {vigencia}'])
    ws.append([])
    ws.append([
        'CÓDIGO', 'DESCRIPCIÓN', 'PPTO APROBADO', 'ADICIONES', 'REDUCCIONES',
        'TRASLADO CRÉDITO', 'CONTRA CRÉDITO', 'APLAZAMIENTOS', 'DESAPLAZAMIENTOS',
        'APROPIACIÓN DEFINITIVA', 'CDP', 'COMPROMISOS', 'ORDENADO', 'PAGADO',
        'SALDO APROPIACIÓN', '% EJECUCIÓN'
    ])

    for r in rubros:
        ej = r.ejecucion
        ws.append([
            r.codigo, r.descripcion,
            float(ej.presupuesto_aprobado), float(ej.adiciones), float(ej.reducciones),
            float(ej.traslado_credito), float(ej.traslado_contra_credito),
            float(ej.aplazamientos), float(ej.desaplazamientos),
            float(ej.apropiacion_definitiva),
            float(ej.cdp), float(ej.compromisos), float(ej.ordenado), float(ej.pagado),
            float(ej.saldo_apropiacion), float(ej.porcentaje_ejecucion),
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=Ejecucion_Gastos_{vigencia}.xlsx'
    wb.save(response)
    return response
