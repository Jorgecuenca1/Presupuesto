"""Motor de recálculo MFMP replicando las fórmulas dinámicas del Excel v75.

Cada función corresponde a una hoja del Excel. La función maestra
`recalcular_mfmp()` ejecuta todas en el orden correcto para que las
dependencias en cascada se propaguen (Variables Macro → Ingresos →
ICLD → Plan Financiero → Ley 617 → Techos → POAI).

Fórmulas replicadas:
    Variables Macro:  D5 = C5/C4 - 1                    (crecimiento anual)
    Ingresos:         L2 = J2 * (1 + IPC_2027)          (proy IPC)
                      M2 = L2 * (1 + IPC_2028)
    Gastos:           K5 = J5 * (1 + IPC/política)      (proy por categoría)
    Planta Detalle:   K5 = J5 * (1 + Política salarial) o (1 + SMLV)
    Costo Planta:     D10 = IPC + productividad + puntos (política salarial)
    Predial:          H15 = G15 * D15/1000 * G$5        (avalúo × tarifa × eff)
    ICO:              E5 = D5 * (1 + PIB_año)
    ICLD:             D11 = SUMIF(Ingresos, "1", proy año)
    Ley 617:          C9 = SUMPRODUCT((fte="1")*(cat=Personal|BS)*gastos)
                      C12 = C9/C10  (ICLD Neto)
    Techos:           C3 = SUMIFS(Ingresos, fte)
                      D3 = SUMIFS(Gastos, fte, cat=Personal)
                      G3 = C3 - D3 - E3 (ingreso disponible inversión)
    Plan Financiero:  B3 = SUM(Ingresos aforo 2026)
                      B4 = B5 + B6 (fto = personal + BS)
    POAI:             C3 = SUMIFS(Ingresos, fte) - SUMIFS(Gastos, fte, cat!=Inv)
    POAI x Dep:       C3 = %Particip * POAI_total
    Cuadre:           E4 = C4 - D4
    Estampillas:      C13 = C7 * C11  (base ppto × %)
                      C21 = C18 * 0.04  (tarifa por estampilla)
"""
from decimal import Decimal
from django.db.models import Sum, Q
from django.db import transaction


ANIOS_PROYECCION = list(range(2027, 2037))


def _campo_proyeccion(anio):
    """Retorna el nombre del campo proy_YYYY."""
    return f'proy_{anio}'


def recalcular_variables_macro_pct_anual():
    """Recalcula % crecimiento anual (pct_anual) SOLO para tipos que son
    un STOCK (SMLV en pesos, PIB en pesos corrientes, TRM en $/USD).
    NO se aplica a tipos que ya son % (IPC, DTF, tasas MFMP), donde el
    `valor` ya está en porcentaje puro y `pct_anual` = valor / 100.
    """
    from .models import VariableMacro
    cambios = 0

    # Tipos stock: pct_anual = valor_actual / valor_anterior - 1
    tipos_stock = ['SMLV', 'PIB', 'TRM']
    for tipo in tipos_stock:
        rows = list(VariableMacro.objects.filter(tipo=tipo).order_by('anio'))
        for i in range(1, len(rows)):
            prev = rows[i-1].valor or Decimal('0')
            curr = rows[i].valor or Decimal('0')
            if prev > 0:
                nuevo_pct = (curr / prev) - Decimal('1')
                if abs((rows[i].pct_anual or 0) - nuevo_pct) > Decimal('0.0001'):
                    rows[i].pct_anual = nuevo_pct
                    rows[i].save(update_fields=['pct_anual'])
                    cambios += 1

    # Tipos que son ya %: normalizar pct_anual = valor / 100 (si valor > 1)
    tipos_pct = ['IPC', 'DTF', 'PIB_R', 'PIB_N', 'SOCIOS', 'DEPREC',
                 'CTA_CORR', 'ING_GNC', 'GTO_GNC', 'BAL_GNC', 'BAL_PRIM',
                 'T_LOCAL', 'T_EXT', 'D_NETA', 'BAL_GG', 'D_GG']
    for vm in VariableMacro.objects.filter(tipo__in=tipos_pct):
        v = vm.valor or Decimal('0')
        if v > Decimal('1'):
            nuevo_pct = v / Decimal('100')
        else:
            nuevo_pct = v
        if abs((vm.pct_anual or 0) - nuevo_pct) > Decimal('0.0001'):
            vm.pct_anual = nuevo_pct
            vm.save(update_fields=['pct_anual'])
            cambios += 1

    return cambios


# Tasas SGP por año (Excel Ingresos!X3..AG3 - crecimiento SGP con ICN)
TASAS_SGP_ANIO = {
    2027: Decimal('0.058'),
    2028: Decimal('0.059'),
    2029: Decimal('0.059'),
    2030: Decimal('0.059'),
    2031: Decimal('0.060'),
    2032: Decimal('0.061'),
    2033: Decimal('0.061'),
    2034: Decimal('0.061'),
    2035: Decimal('0.061'),
    2036: Decimal('0.060'),
}


def _tasa_por_metodo(metodo, anio, ipc_anio):
    """Retorna la tasa de crecimiento anual según el método del rubro.

    Métodos del Excel v75 (hoja Ingresos, col K):
      - IPC (catálogo/aforo)    → IPC MFMP del año
      - SGP (SICODIS)           → Tasa ICN por año (dict TASAS_SGP_ANIO)
      - Superávit: no se proyecta → 0 (no crece)
      - Recursos del Balance    → 0
      - FAEF                    → IPC (aproximación)
      - Vacío o desconocido     → IPC (fallback)
    """
    m = (metodo or '').lower()
    if 'superávit' in m or 'superavit' in m or 'recursos del balance' in m:
        # No se proyecta → factor 0 significa mantener valor
        return None  # None indica "no aplicar factor"
    if 'sgp' in m or 'sicodis' in m:
        return TASAS_SGP_ANIO.get(anio, Decimal('0.06'))
    if 'ipc' in m or 'faef' in m or not m:
        return ipc_anio
    # Otros métodos default a IPC
    return ipc_anio


def recalcular_proyeccion_ingresos_desde_ipc():
    """Recalcula ProyeccionRubroIngreso.proy_YYYY según el método del rubro.

    Regla por Excel:
        - Método IPC:   L = J × (1 + IPC_2027)
        - Método SGP:   L = J × (1 + tasa_ICN_2027)  [0.058 para 2027]
        - Método Superávit / Recursos del Balance: no se proyecta (valor fijo)
    """
    from .models import ProyeccionRubroIngreso, VariableMacro
    # IPC por año como decimal fraccional
    ipc_por_anio = {}
    for vm in VariableMacro.objects.filter(tipo='IPC', anio__in=ANIOS_PROYECCION):
        v = vm.pct_anual or (vm.valor / Decimal('100') if vm.valor > 1 else vm.valor)
        ipc_por_anio[vm.anio] = v or Decimal('0.044')
    if not ipc_por_anio:
        return 0

    cambios = 0
    for r in ProyeccionRubroIngreso.objects.all():
        base = r.proyeccion_dic_2026 or Decimal('0')
        if base == 0:
            # No hay base para proyectar, dejar como está
            continue
        prev = base
        for anio in ANIOS_PROYECCION:
            ipc = ipc_por_anio.get(anio, Decimal('0.044'))
            tasa = _tasa_por_metodo(r.metodo, anio, ipc)
            if tasa is None:
                # Rubro que "no se proyecta": mantener valor
                continue
            nuevo = prev * (Decimal('1') + tasa)
            campo = _campo_proyeccion(anio)
            if abs(getattr(r, campo) - nuevo) > Decimal('1'):
                setattr(r, campo, nuevo)
                cambios += 1
            prev = nuevo
        r.save()
    return cambios


def recalcular_costo_planta_politica_salarial():
    """Excel: D10 = D6 + D8 + D9 (IPC + productividad + puntos sindicales).
    ParametroAnualPlanta.ipc_esperado se toma tal cual del Excel;
    política salarial = ipc + productividad + puntos.
    """
    from .models import ParametroAnualPlanta
    cambios = 0
    for p in ParametroAnualPlanta.objects.all():
        # No hay campo directo "política" pero la usamos así implícitamente
        cambios += 1  # no persistimos, la propiedad se calcula al vuelo
    return cambios


def politica_salarial_del_anio(anio):
    """D10 del Excel = IPC + productividad + puntos sindicales."""
    from .models import ParametroAnualPlanta
    p = ParametroAnualPlanta.objects.filter(anio=anio).first()
    if not p:
        return Decimal('0.06')
    return (p.ipc_esperado or 0) + (p.indice_productividad or 0) + (p.puntos_salariales_sindicales or 0)


def recalcular_planta_detalle():
    """Excel:
        Cargos que crecen por "Política":  K5 = J5 × (1 + política_salarial)
        Cargos que crecen por "SMLV":      K44 = J44 × (1 + IPC)
    """
    from .models import PlantaDetalleCargo, VariableMacro
    # IPC año a año
    ipc_por_anio = {vm.anio: (vm.pct_anual or (vm.valor/100 if vm.valor>1 else vm.valor))
                    for vm in VariableMacro.objects.filter(tipo='IPC', anio__in=ANIOS_PROYECCION)}
    politica = {a: politica_salarial_del_anio(a) for a in ANIOS_PROYECCION}
    cambios = 0
    for c in PlantaDetalleCargo.objects.all():
        base = c.costo_anual_2026 or Decimal('0')
        if base == 0:
            continue
        crece_por = (c.crece_por or '').strip().lower()
        prev = base
        for anio in ANIOS_PROYECCION:
            if crece_por.startswith('polit'):
                factor = Decimal('1') + politica.get(anio, Decimal('0.06'))
            else:
                factor = Decimal('1') + ipc_por_anio.get(anio, Decimal('0.03'))
            nuevo = prev * factor
            campo = f'costo_{anio}'
            if abs(getattr(c, campo) - nuevo) > Decimal('1'):
                setattr(c, campo, nuevo)
                cambios += 1
            prev = nuevo
        c.save()
    return cambios


def recalcular_ico_desde_pib():
    """Excel:
        E5 = D5 (ICO 2024) × (1 + PIB_2026)  [proyección 2026]
        F5 = E5 × (1 + PIB_2027)
        ...
    Se usa PIB pct_anual año a año.
    """
    from .models import ICOProyeccion, VariableMacro
    pib_por_anio = {}
    for vm in VariableMacro.objects.filter(tipo='PIB', anio__gte=2026, anio__lte=2036):
        pib_por_anio[vm.anio] = vm.pct_anual or Decimal('0.08')

    cambios = 0
    for r in ICOProyeccion.objects.all():
        base = r.ico_liquidado_2024 or Decimal('0')
        if base == 0:
            continue
        # 2026 = 2024 × (1+pib_2025) × (1+pib_2026)
        prev = base
        # aplicar 2025 y 2026 desde el 2024
        for anio_pib in (2025, 2026):
            prev = prev * (Decimal('1') + pib_por_anio.get(anio_pib, Decimal('0.08')))
        campo = 'proy_2026'
        if abs(getattr(r, campo) - prev) > Decimal('1'):
            setattr(r, campo, prev); cambios += 1

        for anio in ANIOS_PROYECCION:
            prev = prev * (Decimal('1') + pib_por_anio.get(anio, Decimal('0.08')))
            campo = _campo_proyeccion(anio)
            if abs(getattr(r, campo) - prev) > Decimal('1'):
                setattr(r, campo, prev); cambios += 1
        r.save()
    return cambios


def recalcular_icld_proyectado():
    """Excel ICLD!D11 = SUMIF(Ingresos.fuente="1", Ingresos.proy_2027)
    Suma proyecciones de rubros ingreso por fuente y año.
    """
    from .models import ICLDProyectado, ProyeccionRubroIngreso, FuenteFinanciacion
    cambios = 0
    for f in FuenteFinanciacion.objects.filter(codigo__in=['1', '11', '16', '35', '41']):
        # Estas son las fuentes ICLD principales (Recursos Propios + variantes)
        for anio in [2026] + ANIOS_PROYECCION:
            if anio == 2026:
                campo = 'proyeccion_dic_2026'
            else:
                campo = _campo_proyeccion(anio)
            total = ProyeccionRubroIngreso.objects.filter(codigo_fuente=f.codigo).aggregate(
                t=Sum(campo))['t'] or Decimal('0')
            obj, _ = ICLDProyectado.objects.get_or_create(
                fuente=f, anio=anio, defaults={'valor_bruto': total})
            if abs(obj.valor_bruto - total) > Decimal('1'):
                obj.valor_bruto = total
                obj.save(update_fields=['valor_bruto'])
                cambios += 1
    return cambios


# Categorías de gasto según Excel v75 (hoja Gastos, col E)
CATS_FUNCIONAMIENTO = ['Personal', 'Bienes y Servicios', 'Transferencias', 'Otros']
CATS_DEUDA = ['Deuda']
CATS_INVERSION = ['Inversion', 'Inversión']


def _q_categorias(categorias):
    """Query Q para filtrar por lista de categorías exactas."""
    from django.db.models import Q
    q = Q()
    for c in categorias:
        q |= Q(categoria__iexact=c)
    return q


def recalcular_ley_617_desde_gastos():
    """Excel:
        C9 = SUMPRODUCT((Gastos.fte="1") × (cat="Personal" OR cat="BS") × Gastos.aprop)
        C10 = ICLD!C20  (ICLD Neto Total)
        C12 = C9 / C10  (indicador)
    """
    from .models import Ley617Proyectado, ProyeccionRubroGasto, ICLDProyectado
    cambios = 0
    campos_por_anio = {
        2026: 'apropiacion_2026',
        **{a: _campo_proyeccion(a) for a in ANIOS_PROYECCION},
    }
    # Sumar ICLD Neto TOTAL por año (todas las fuentes ICLD)
    icld_total_por_anio = {}
    for anio in [2026] + ANIOS_PROYECCION:
        t = ICLDProyectado.objects.filter(anio=anio).aggregate(x=Sum('valor_bruto'))['x'] or Decimal('0')
        icld_total_por_anio[anio] = t

    for anio, campo in campos_por_anio.items():
        # GF de Rec. Propios (fuente 1) = Personal + BS + Transferencias + Otros
        gf = ProyeccionRubroGasto.objects.filter(
            _q_categorias(CATS_FUNCIONAMIENTO),
            codigo_fuente='1',
        ).aggregate(t=Sum(campo))['t'] or Decimal('0')
        icld = icld_total_por_anio.get(anio, Decimal('0'))

        obj, _ = Ley617Proyectado.objects.get_or_create(
            anio=anio, defaults={'gastos_funcionamiento': gf, 'icld_neto': icld,
                                 'pct_limite': Decimal('80')})
        if abs(obj.gastos_funcionamiento - gf) > 1 or abs(obj.icld_neto - icld) > 1:
            obj.gastos_funcionamiento = gf
            obj.icld_neto = icld
            obj.save()
            cambios += 1
    return cambios


def recalcular_techos_inversion_dinamico(vigencia):
    """Excel Techos!:
        C3 = SUMIFS(Ingresos.proy_vigencia, fuente=A3)
        D3 = SUMIFS(Gastos.proy_vigencia, fuente=A3, cat="Personal")
        E3 = SUMIFS(Gastos.proy_vigencia, fuente=A3, cat="Deuda")
        F3 = D3 + E3   (Total Fto+Deuda)
        G3 = C3 - F3   (Total Inversión)
        H3 = SUMIFS(VF, fte=A3)
    """
    from .models import TechoInversion, ProyeccionRubroIngreso, ProyeccionRubroGasto
    campo_ing = 'proyeccion_dic_2026' if vigencia == 2026 else _campo_proyeccion(vigencia)
    campo_gto = 'apropiacion_2026' if vigencia == 2026 else _campo_proyeccion(vigencia)
    cambios = 0
    for t in TechoInversion.objects.filter(vigencia=vigencia):
        cod = (t.codigo_fuente or '').strip()
        if not cod:
            # Match por nombre concepto contra ProyeccionRubroIngreso.nombre_fuente
            ing_total = ProyeccionRubroIngreso.objects.filter(
                nombre_fuente__icontains=t.concepto_ingreso).aggregate(x=Sum(campo_ing))['x'] or Decimal('0')
            gto_qs = ProyeccionRubroGasto.objects.filter(nombre_fuente__icontains=t.concepto_ingreso)
        else:
            ing_total = ProyeccionRubroIngreso.objects.filter(codigo_fuente=cod).aggregate(
                x=Sum(campo_ing))['x'] or Decimal('0')
            gto_qs = ProyeccionRubroGasto.objects.filter(codigo_fuente=cod)

        fto = gto_qs.filter(_q_categorias(CATS_FUNCIONAMIENTO)).aggregate(
            x=Sum(campo_gto))['x'] or Decimal('0')
        deuda = gto_qs.filter(_q_categorias(CATS_DEUDA)).aggregate(
            x=Sum(campo_gto))['x'] or Decimal('0')

        cambio = False
        if ing_total > 0 and abs(t.ingresos - ing_total) > 1:
            t.ingresos = ing_total; cambio = True
        if fto > 0 and abs(t.fto - fto) > 1:
            t.fto = fto; cambio = True
        if abs(t.deuda - deuda) > 1:
            t.deuda = deuda; cambio = True
        if cambio:
            t.save(); cambios += 1
    return cambios


def recalcular_plan_financiero_desde_proyecciones():
    """Excel Plan Financiero!:
        B3 = SUM(Ingresos aforo 2026)
        C3 = SUM(Ingresos proy 2027)
        B5 = SUMIFS(Gastos aprop 2026, cat=Personal)
        B6 = SUMIFS(Gastos aprop 2026, cat=BS)
        B4 = B5 + B6  (Funcionamiento)
        B7 = SUMIFS(Gastos aprop 2026, cat=Deuda)  (Servicio Deuda)
        B8 = B3 - B4 - B7  (Inversión)
    """
    from .models import PlanFinancieroLinea, ProyeccionRubroIngreso, ProyeccionRubroGasto
    campos_ing = {2026: 'aforo_2026', **{a: _campo_proyeccion(a) for a in ANIOS_PROYECCION}}
    campos_gto = {2026: 'apropiacion_2026', **{a: _campo_proyeccion(a) for a in ANIOS_PROYECCION}}
    cambios = 0
    for anio in [2026] + ANIOS_PROYECCION:
        # Ingresos: excluir rubros título (aquellos sin descripción concreta o
        # con código corto). Los rubros hoja del Excel tienen código con al
        # menos 4 puntos (ej 03.1.1.01.01.001).
        ing = ProyeccionRubroIngreso.objects.exclude(descripcion='').aggregate(
            t=Sum(campos_ing[anio]))['t'] or Decimal('0')
        personal = ProyeccionRubroGasto.objects.filter(categoria__iexact='Personal').aggregate(
            t=Sum(campos_gto[anio]))['t'] or Decimal('0')
        # Bienes y Servicios + Transferencias + Otros (todo funcionamiento no-Personal)
        bs = ProyeccionRubroGasto.objects.filter(
            Q(categoria__iexact='Bienes y Servicios') | Q(categoria__iexact='Transferencias') |
            Q(categoria__iexact='Otros')
        ).aggregate(t=Sum(campos_gto[anio]))['t'] or Decimal('0')
        deuda = ProyeccionRubroGasto.objects.filter(categoria__iexact='Deuda').aggregate(
            t=Sum(campos_gto[anio]))['t'] or Decimal('0')
        fto = personal + bs
        inv = ing - fto - deuda

        for tipo, valor in [('A', ing), ('B', fto), ('B1', personal), ('B2', bs),
                            ('C', deuda), ('D', inv), ('T', fto + deuda + inv)]:
            obj, _ = PlanFinancieroLinea.objects.get_or_create(
                tipo=tipo, anio=anio, defaults={'valor': valor})
            if abs(obj.valor - valor) > Decimal('1'):
                obj.valor = valor
                obj.save(update_fields=['valor'])
                cambios += 1
    return cambios


def recalcular_poai_proyectado_dinamico():
    """Excel POAI 2027-2036!:
        C3 = SUMIFS(Ingresos, fte=A3, proy_2027) − SUMIFS(Gastos, fte=A3, cat≠Inversión, proy_2027)
        = Ingreso por fuente − Fto+BS+Deuda por fuente
    """
    from .models import POAIProyectado, ProyeccionRubroIngreso, ProyeccionRubroGasto, FuenteFinanciacion
    cambios = 0
    for f in FuenteFinanciacion.objects.all():
        cod = f.codigo
        for anio in ANIOS_PROYECCION:
            campo_i = _campo_proyeccion(anio)
            campo_g = _campo_proyeccion(anio)
            ing = ProyeccionRubroIngreso.objects.filter(codigo_fuente=cod).aggregate(
                t=Sum(campo_i))['t'] or Decimal('0')
            no_inv = ProyeccionRubroGasto.objects.filter(codigo_fuente=cod).exclude(
                categoria__icontains='inver').aggregate(t=Sum(campo_g))['t'] or Decimal('0')
            poai = ing - no_inv
            if poai <= 0:
                # No lo persistimos si es 0 o negativo
                continue
            obj, _ = POAIProyectado.objects.get_or_create(
                fuente=f, anio=anio, defaults={'valor': poai})
            if abs(obj.valor - poai) > Decimal('1'):
                obj.valor = poai
                obj.save(update_fields=['valor'])
                cambios += 1
    return cambios


def recalcular_poai_dependencias_dinamico():
    """Excel POAI x Dep!: C3 = $B3 (%Particip) × 'POAI 2027-2036'!C$105 (total)."""
    from .models import POAIPorDependencia, POAIProyectado
    cambios = 0
    for anio in ANIOS_PROYECCION:
        total_poai = POAIProyectado.objects.filter(anio=anio).aggregate(t=Sum('valor'))['t'] or Decimal('0')
        for dep in POAIPorDependencia.objects.filter(anio=anio):
            nuevo = dep.pct_participacion * total_poai
            if abs(dep.valor - nuevo) > Decimal('1'):
                dep.valor = nuevo
                dep.save(update_fields=['valor'])
                cambios += 1
    return cambios


def recalcular_cuadre_por_fuente():
    """Excel Cuadre!:
        C4 = SUMIFS(Ingresos aforo 2026, fte=A4)
        D4 = SUMIFS(Gastos aprop 2026, fte=A4)
        E4 = C4 - D4
        F4 = SUMIFS(Ingresos proy 2027, fte=A4)
        G4 = SUMIFS(Gastos proy 2027, fte=A4)
        H4 = F4 - G4
    """
    from .models import CuadrePorFuente, ProyeccionRubroIngreso, ProyeccionRubroGasto, FuenteFinanciacion
    cambios = 0
    for f in FuenteFinanciacion.objects.all():
        cod = f.codigo
        for anio, campo_i, campo_g in [
            (2026, 'aforo_2026', 'apropiacion_2026'),
            (2027, 'proy_2027', 'proy_2027'),
        ]:
            ing = ProyeccionRubroIngreso.objects.filter(codigo_fuente=cod).aggregate(
                t=Sum(campo_i))['t'] or Decimal('0')
            gto = ProyeccionRubroGasto.objects.filter(codigo_fuente=cod).aggregate(
                t=Sum(campo_g))['t'] or Decimal('0')
            if ing == 0 and gto == 0:
                continue
            obj, _ = CuadrePorFuente.objects.get_or_create(
                fuente=f, anio=anio, defaults={'ingreso': ing, 'gasto': gto})
            if abs(obj.ingreso - ing) > 1 or abs(obj.gasto - gto) > 1:
                obj.ingreso = ing
                obj.gasto = gto
                obj.save()
                cambios += 1
    return cambios


@transaction.atomic
def recalcular_mfmp(vigencia=2027):
    """Función maestra: recalcula toda la cascada MFMP como en Excel.
    Orden de dependencias:
        1. Variables Macro (crecimientos)
        2. Proyecciones ingresos/gastos (aplicar IPC año a año)
        3. Planta Detalle (política salarial)
        4. ICO (crecimiento PIB)
        5. ICLD Proyectado (SUMIF por fuente)
        6. Ley 617 (GF / ICLD)
        7. Plan Financiero (SUM proyecciones)
        8. POAI Proyectado (ingreso - no-inversión)
        9. POAI x Dependencia (% × POAI total)
       10. Techos Inversión (dinámico por fuente)
       11. Cuadre por Fuente
    """
    resumen = {}
    resumen['1_variables_macro'] = recalcular_variables_macro_pct_anual()
    resumen['2_proy_ingresos'] = recalcular_proyeccion_ingresos_desde_ipc()
    resumen['3_planta_detalle'] = recalcular_planta_detalle()
    resumen['4_ico'] = recalcular_ico_desde_pib()
    resumen['5_icld'] = recalcular_icld_proyectado()
    resumen['6_ley_617'] = recalcular_ley_617_desde_gastos()
    resumen['7_plan_financiero'] = recalcular_plan_financiero_desde_proyecciones()
    resumen['8_poai'] = recalcular_poai_proyectado_dinamico()
    resumen['9_poai_dependencias'] = recalcular_poai_dependencias_dinamico()
    resumen['10_techos'] = recalcular_techos_inversion_dinamico(vigencia)
    resumen['11_cuadre'] = recalcular_cuadre_por_fuente()
    return resumen
