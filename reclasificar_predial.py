"""Reclasifica los ContribuyentePredial leyendo el Excel original y emparejando por cedula_catastral.

Regla correcta:
  - CABECERA MUNICIPAL → urbano (UV/UED/UEF/UNEU/UNUE/UNNU según destino)
  - Corregimientos (PACHAQUIARO, PUERTO GUADALUPE, etc.) → rural (RU)
  - RURAL → RU
  - CLASE con 'PARCELACION' o 'FINCA' → PE / PNE (independiente de tipo)
"""
import argparse
import os

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'presupuesto_project.settings')
django.setup()

import openpyxl
from ingresos.models import ContribuyentePredial


# Destinos exentos de predial (bienes de uso público / institucionales no tributarios)
DESTINOS_EXENTOS = {
    'USO PUBLICO', 'INFRAESTRUCTURA_HIDRAULICA', 'INFRAESTRUCTURA_TRANSPORTE',
    'SERVICIOS_FUNERARIOS', 'CULTUTAL', 'CULTURAL',
}

# Destinos urbanos edificados "no vivienda" (UED)
DESTINOS_URBANO_EDIF_DEMAS = {
    'COMERCIAL', 'INDUSTRIAL', 'INSTITUCIONAL', 'EDUCATIVO',
    'RECREACIONAL', 'SALUBRIDAD', 'RELIGIOSO',
}


def clasificar(tipo, destino, clase):
    tipo = (tipo or '').strip().upper()
    destino = (destino or '').strip().upper()
    clase = (clase or '').strip().upper()
    es_parcelacion = 'PARCELACION' in clase or 'FINCA' in clase
    es_no_edif_clase = 'NO EDIFICAD' in clase

    if es_parcelacion:
        return 'PNE' if es_no_edif_clase else 'PE'

    if tipo != 'CABECERA MUNICIPAL':
        # RURAL o cualquier corregimiento → rural
        return 'RU'

    # CABECERA MUNICIPAL
    # Exentos: bienes de uso público / infraestructura / funerarios / cultural → RU
    if destino in DESTINOS_EXENTOS:
        return 'RU'

    if 'FINANCIERA' in clase:
        return 'UEF'
    if destino == 'HABITACIONAL':
        return 'UV'
    if 'LOTE' in destino:
        if 'NO URBANIZABLE' in destino:
            return 'UNNU'
        if 'URBANIZABLE NO URBAN' in destino:
            return 'UNEU'
        if destino == 'LOTE URBANIZADO NO CONST':
            return 'UNUE'
        return 'UNEU'
    if destino in DESTINOS_URBANO_EDIF_DEMAS:
        return 'UED'
    # Cualquier otro destino en cabecera → UED por defecto
    return 'UED'


def run(archivo, vigencia=2026, dry_run=False):
    wb = openpyxl.load_workbook(archivo, data_only=True, read_only=True)
    ws = wb.active

    mapa = {}
    for row in ws.iter_rows(min_row=8, values_only=True):
        if not row or not row[0] or len(row) < 15:
            continue
        ref = str(row[0]).strip()[:50]
        tipo = str(row[12] or '')
        destino = str(row[13] or '')
        clase = str(row[14] or '')
        mapa[ref] = clasificar(tipo, destino, clase)

    print(f'Excel: {len(mapa)} cedulas catastrales únicas')

    cambios = {}
    antes = {}
    despues = {}
    updates = []
    sin_match = 0

    qs = ContribuyentePredial.objects.filter(vigencia=vigencia)
    total = qs.count()
    print(f'DB: {total} registros en vigencia {vigencia}')

    for c in qs.iterator(chunk_size=1000):
        antes[c.categoria] = antes.get(c.categoria, 0) + 1
        nueva = mapa.get(c.cedula_catastral)
        if nueva is None:
            # Registro manual sin match en Excel: mantener
            nueva = c.categoria
            sin_match += 1
        despues[nueva] = despues.get(nueva, 0) + 1
        if nueva != c.categoria:
            cambios[(c.categoria, nueva)] = cambios.get((c.categoria, nueva), 0) + 1
            if not dry_run:
                c.categoria = nueva
                updates.append(c)
                if len(updates) >= 1000:
                    ContribuyentePredial.objects.bulk_update(updates, ['categoria'])
                    updates = []
    if updates and not dry_run:
        ContribuyentePredial.objects.bulk_update(updates, ['categoria'])

    print('\n== ANTES ==')
    for k, v in sorted(antes.items()):
        print(f'  {k}: {v}')
    print('\n== DESPUÉS ==')
    for k, v in sorted(despues.items()):
        print(f'  {k}: {v}')
    print('\n== Reclasificaciones ==')
    for (a, b), n in sorted(cambios.items(), key=lambda x: -x[1]):
        print(f'  {a} → {b}: {n}')
    print(f'\nSin match en Excel (mantenidos): {sin_match}')

    URB = {'UV', 'UED', 'UEF', 'UNEU', 'UNUE', 'UNNU'}
    urb = sum(v for k, v in despues.items() if k in URB)
    rur = sum(v for k, v in despues.items() if k not in URB)
    print(f'\nTotal URBANO: {urb}')
    print(f'Total RURAL:  {rur}')
    if dry_run:
        print('\n(DRY-RUN: no se guardó nada)')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('archivo', help='Excel original Tabla Predial Comparativo')
    p.add_argument('--vigencia', type=int, default=2026)
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()
    run(args.archivo, args.vigencia, args.dry_run)
