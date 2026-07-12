"""Importa Sistema_MFMP_PuertoLopez_v75.xlsx a la BD (modelos MFMP nuevos).

Uso:
    python import_mfmp_v75.py [/ruta/al/xlsx]

Carga:
    - Fuentes (catálogo maestro)
    - Plan Financiero (10 años A/B/C/D)
    - ICLD proyectado 10 años por fuente
    - Ley 617 proyectada
    - POAI 10 años por fuente
    - POAI por dependencia
    - Cuadre por fuente
    - Saldo VF por fuente
    - Ingresos corrientes Ley 358
"""
import os, sys, warnings
warnings.filterwarnings('ignore')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'presupuesto_project.settings')
import django; django.setup()
from decimal import Decimal, InvalidOperation
from openpyxl import load_workbook
from core.models import (
    FuenteFinanciacion, PlanFinancieroLinea, ICLDProyectado,
    Ley617Proyectado, POAIProyectado, POAIPorDependencia,
    CuadrePorFuente, SaldoVFPorFuente, IngresoCorrienteLey358,
    ParametrosSistema,
)


def D(v):
    if v is None or v == '':
        return Decimal('0')
    try:
        return Decimal(str(v))
    except (InvalidOperation, ValueError):
        return Decimal('0')


def importar(xlsx_path):
    wb = load_workbook(xlsx_path, data_only=True)

    # ═══ 1) FUENTES (catálogo) ═══════════════════════════════════════════
    ws = wb['Fuentes']
    n = 0
    for r in range(2, ws.max_row + 1):
        cod = ws.cell(row=r, column=1).value
        nom = ws.cell(row=r, column=2).value
        if not cod or not nom:
            continue
        FuenteFinanciacion.objects.update_or_create(
            codigo=str(cod).strip(),
            defaults={'nombre': str(nom).strip(), 'activo': True},
        )
        n += 1
    print(f'✓ Fuentes:                       {n:>5}')

    # ═══ 2) PLAN FINANCIERO ══════════════════════════════════════════════
    ws = wb['Plan Financiero']
    # Headers en F2: cols 2..12 = 2026..2036
    anios = [ws.cell(row=2, column=c).value for c in range(2, 13)]
    anios = [int(a) for a in anios if a]
    MAPA = {
        'A. INGRESOS TOTALES': 'A',
        'B. FUNCIONAMIENTO': 'B',
        '   B.1 Personal': 'B1',
        '   B.2 Bienes, Servicios y Otros': 'B2',
        'C. SERVICIO DE LA DEUDA': 'C',
        'D. INVERSIÓN (= A − B − C)': 'D',
        'Total Gastos (B+C+D)': 'T',
    }
    n = 0
    for r in range(3, ws.max_row + 1):
        concepto = ws.cell(row=r, column=1).value
        if not concepto:
            continue
        tipo = MAPA.get(str(concepto))
        if not tipo:
            # tolerar espacios/prefijos leves
            for k, v in MAPA.items():
                if str(concepto).strip().startswith(k.strip()[:20]):
                    tipo = v; break
        if not tipo:
            continue
        for i, anio in enumerate(anios):
            val = D(ws.cell(row=r, column=2 + i).value)
            PlanFinancieroLinea.objects.update_or_create(
                tipo=tipo, anio=anio, defaults={'valor': val},
            )
            n += 1
    print(f'✓ Plan Financiero (celdas):      {n:>5}')

    # ═══ 3) ICLD PROYECTADO ══════════════════════════════════════════════
    ws = wb['ICLD']
    # Headers están en F10 (2026-2036 desde col 3)
    row_h = 10
    anios = [ws.cell(row=row_h, column=c).value for c in range(3, 14)]
    anios = [int(a) for a in anios if a]
    n = 0
    for r in range(11, ws.max_row + 1):
        concepto = ws.cell(row=r, column=2).value
        if not concepto:
            continue
        concepto_s = str(concepto).strip().upper()
        # Solo capturamos "Total Fuente N (...)"
        if 'TOTAL FUENTE' not in concepto_s:
            continue
        # Extraer código
        try:
            cod = concepto_s.split('FUENTE')[1].split('(')[0].strip()
        except Exception:
            continue
        fuente = FuenteFinanciacion.objects.filter(codigo=cod).first()
        if not fuente:
            continue
        for i, anio in enumerate(anios):
            val = D(ws.cell(row=r, column=3 + i).value)
            ICLDProyectado.objects.update_or_create(
                fuente=fuente, anio=anio,
                defaults={'valor_bruto': val},
            )
            n += 1
    print(f'✓ ICLD Proyectado (celdas):      {n:>5}')

    # ═══ 4) LEY 617 PROYECTADO ═══════════════════════════════════════════
    ws = wb['Ley 617']
    # Headers en F8 (col 3..13 = 2026..2036)
    row_h = 8
    anios = [ws.cell(row=row_h, column=c).value for c in range(3, 14)]
    anios = [int(a) for a in anios if a]
    # F9: Gastos de Funcionamiento, F10: ICLD Neto
    gf_row = None; icld_row = None; pct_row = None
    for r in range(9, min(ws.max_row + 1, 14)):
        c = ws.cell(row=r, column=2).value
        if not c: continue
        cs = str(c).lower()
        if 'gasto' in cs and 'funcion' in cs: gf_row = r
        elif 'icld' in cs and 'neto' in cs: icld_row = r
        elif 'limite' in cs or 'límite' in cs: pct_row = r
    if gf_row and icld_row:
        n = 0
        for i, anio in enumerate(anios):
            gf = D(ws.cell(row=gf_row, column=3 + i).value)
            icld = D(ws.cell(row=icld_row, column=3 + i).value)
            pct = D(ws.cell(row=pct_row, column=3 + i).value) if pct_row else Decimal('80')
            Ley617Proyectado.objects.update_or_create(
                anio=anio,
                defaults={'gastos_funcionamiento': gf, 'icld_neto': icld,
                          'pct_limite': pct if pct > 0 else Decimal('80')},
            )
            n += 1
        print(f'✓ Ley 617 Proyectado (años):     {n:>5}')

    # ═══ 5) POAI 2027-2036 por fuente ════════════════════════════════════
    ws = wb['POAI 2027-2036']
    # Headers en F2 col 3..12 = 2027..2036
    anios = [ws.cell(row=2, column=c).value for c in range(3, 13)]
    anios = [int(a) for a in anios if a]
    n = 0
    for r in range(3, ws.max_row + 1):
        cod = ws.cell(row=r, column=1).value
        if not cod: continue
        fuente = FuenteFinanciacion.objects.filter(codigo=str(cod).strip()).first()
        if not fuente: continue
        for i, anio in enumerate(anios):
            val = D(ws.cell(row=r, column=3 + i).value)
            if val == 0: continue
            POAIProyectado.objects.update_or_create(
                fuente=fuente, anio=anio,
                defaults={'valor': val},
            )
            n += 1
    print(f'✓ POAI Proyectado (celdas):      {n:>5}')

    # ═══ 6) POAI x DEPENDENCIA ═══════════════════════════════════════════
    ws = wb['POAI x Dependencia']
    anios = [ws.cell(row=2, column=c).value for c in range(3, 13)]
    anios = [int(a) for a in anios if a]
    n = 0
    for r in range(3, ws.max_row + 1):
        dep = ws.cell(row=r, column=1).value
        pct = ws.cell(row=r, column=2).value
        if not dep: continue
        for i, anio in enumerate(anios):
            val = D(ws.cell(row=r, column=3 + i).value)
            POAIPorDependencia.objects.update_or_create(
                dependencia=str(dep).strip(), anio=anio,
                defaults={'pct_participacion': D(pct), 'valor': val},
            )
            n += 1
    print(f'✓ POAI Dependencias (celdas):    {n:>5}')

    # ═══ 7) CUADRE POR FUENTE ════════════════════════════════════════════
    ws = wb['Cuadre por Fuente']
    # F3 headers: cols 3=Ing 2026, 4=Gto 2026, 6=Ing 2027, 7=Gto 2027
    n = 0
    for r in range(4, ws.max_row + 1):
        cod = ws.cell(row=r, column=1).value
        if not cod: continue
        fuente = FuenteFinanciacion.objects.filter(codigo=str(cod).strip()).first()
        if not fuente: continue
        # 2026
        ing_26 = D(ws.cell(row=r, column=3).value)
        gto_26 = D(ws.cell(row=r, column=4).value)
        CuadrePorFuente.objects.update_or_create(
            fuente=fuente, anio=2026,
            defaults={'ingreso': ing_26, 'gasto': gto_26},
        )
        # 2027
        ing_27 = D(ws.cell(row=r, column=6).value)
        gto_27 = D(ws.cell(row=r, column=7).value)
        CuadrePorFuente.objects.update_or_create(
            fuente=fuente, anio=2027,
            defaults={'ingreso': ing_27, 'gasto': gto_27},
        )
        n += 2
    print(f'✓ Cuadre por Fuente (registros): {n:>5}')

    # ═══ 8) SALDO VF POR FUENTE ══════════════════════════════════════════
    ws = wb['Saldo VF por Fuente']
    # F3 headers
    anio_ref = ws.cell(row=1, column=14).value
    try: anio_ref = int(anio_ref)
    except (TypeError, ValueError): anio_ref = 2026
    n = 0
    for r in range(4, ws.max_row + 1):
        cod = ws.cell(row=r, column=1).value
        if not cod: continue
        fuente = FuenteFinanciacion.objects.filter(codigo=str(cod).strip()).first()
        if not fuente: continue
        SaldoVFPorFuente.objects.update_or_create(
            fuente=fuente, anio_referencia=anio_ref,
            defaults={
                'apropiacion_definitiva': D(ws.cell(row=r, column=4).value),
                'cdp_vigentes': D(ws.cell(row=r, column=6).value),
                'vf_aprobadas': D(ws.cell(row=r, column=7).value),
                'vf_en_tramite': D(ws.cell(row=r, column=8).value),
                'vf_solicitada': D(ws.cell(row=r, column=10).value),
            },
        )
        n += 1
    print(f'✓ Saldo VF por Fuente:           {n:>5}')

    # ═══ 9) INGRESOS CORRIENTES LEY 358 ══════════════════════════════════
    ws = wb['Ing Corrientes Ley 358']
    n = 0
    for r in range(4, ws.max_row + 1):
        cod = ws.cell(row=r, column=1).value
        desc = ws.cell(row=r, column=2).value
        fte = ws.cell(row=r, column=3).value
        if not cod or not desc: continue
        IngresoCorrienteLey358.objects.update_or_create(
            codigo_ccpet=str(cod).strip(),
            fuente=str(fte or '').strip(),
            defaults={
                'descripcion': str(desc).strip()[:300],
                'ejec_2024': D(ws.cell(row=r, column=4).value),
                'ejec_2025': D(ws.cell(row=r, column=5).value),
                'aforo_2026': D(ws.cell(row=r, column=6).value),
                'aplica_ley_358': bool(int(D(ws.cell(row=r, column=7).value))),
            },
        )
        n += 1
    print(f'✓ Ing Corrientes Ley 358:        {n:>5}')

    # ═══ Sincronizar ICLD calculado de ParametrosSistema desde Plan Financiero
    # (usuario pidió: ICLD 2027 debe venir del Plan Financiero proyectado 2027-2036)
    p = ParametrosSistema.objects.filter(activo=True).first()
    if p:
        # ICLD 2027 total = fuente "RECURSOS PROPIOS" (código 1) del ICLDProyectado
        icld_2027 = ICLDProyectado.objects.filter(
            fuente__codigo='1', anio=p.vigencia,
        ).first()
        if icld_2027 and icld_2027.valor_bruto > 0:
            p.icld_calculado = icld_2027.valor_bruto
            p.save(update_fields=['icld_calculado'])
            print(f'✓ ICLD ParametrosSistema (2027): ${p.icld_calculado:,.0f}')


if __name__ == '__main__':
    ruta = sys.argv[1] if len(sys.argv) > 1 else '/Users/jorgebinkio/Downloads/Sistema_MFMP_PuertoLopez_v75.xlsx'
    if not os.path.isfile(ruta):
        print(f'No existe: {ruta}')
        sys.exit(1)
    print(f'Importando: {ruta}\n')
    importar(ruta)
    print('\n=== IMPORT COMPLETADO ===')
