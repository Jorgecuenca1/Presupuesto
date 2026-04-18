"""
Importa registros de la Tabla Predial Comparativo (vigencia actual) al modelo ContribuyentePredial.

Fuente: 'Tabla Predial Comparativo con vigencia anterior (5) (1).xlsx'
Columnas relevantes (encabezados en fila 7, datos desde fila 8):
  col 1:  REFERENCIA CATASTRAL (cedula_catastral)
  col 11: PROPIETARIO TITULAR (actual)
  col 12: DIRECCION
  col 13: TIPO (CABECERA MUNICIPAL / RURAL / corregimiento)
  col 14: DESTINO (HABITACIONAL, COMERCIAL, INDUSTRIAL, AGROPECUARIO, LOTE ...)
  col 15: CLASE (PARCELACIONES / NO EDIFICADOS / ACTIVIDADES FINANCIERAS ...)
  col 23: AVALUO (vigencia actual)

Mapea destino/clase/tipo → categoría del sistema:
  UV   Urbano - Vivienda
  UEF  Urbano Edificado - Act. Financieras
  UED  Urbano Edificado - Demás
  UNEU Urbano No Edificado - Urbanizable No Urbanizado
  UNUE Urbano No Edificado - Urbanizado No Edificado
  UNNU Urbano No Edificado - No Urbanizable
  RU   Rural
  PE   Parcelación/Finca Recreo - Edificado
  PNE  Parcelación/Finca Recreo - No Edificado

Uso:
  python import_predial.py <archivo.xlsx> [--vigencia 2026] [--replace]
  --replace borra primero los ContribuyentePredial de la vigencia antes de importar.
"""
import argparse
import os
import sys
from decimal import Decimal, InvalidOperation

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'presupuesto_project.settings')
django.setup()

import openpyxl
from ingresos.models import ContribuyentePredial


URBANO_TIPOS = {
    # Solo CABECERA MUNICIPAL es urbano. Corregimientos son rurales.
    'CABECERA MUNICIPAL',
}


def clasificar(tipo, destino, clase):
    tipo = (tipo or '').strip().upper()
    destino = (destino or '').strip().upper()
    clase = (clase or '').strip().upper()

    is_urbano = tipo in URBANO_TIPOS
    is_parcelacion = 'PARCELACION' in clase or 'FINCA' in clase
    is_financiero = 'FINANCIERA' in clase or 'FINANCIER' in clase
    is_no_edif_clase = 'NO EDIFICAD' in clase

    is_lote = 'LOTE' in destino
    is_urbanizable_no_urbanizado = 'URBANIZABLE NO URBAN' in destino
    is_no_urbanizable = 'NO URBANIZABLE' in destino
    is_urbanizado_no_edif = destino == 'LOTE URBANIZADO NO CONST'
    is_habitacional = destino == 'HABITACIONAL'

    # Parcelación / Finca de Recreo (rural, por clase)
    if is_parcelacion:
        if is_no_edif_clase:
            return 'PNE'
        return 'PE'

    if is_urbano:
        # Urbano
        if is_financiero:
            return 'UEF'
        if is_habitacional:
            return 'UV'
        if is_lote:
            if is_no_urbanizable:
                return 'UNNU'
            if is_urbanizable_no_urbanizado:
                return 'UNEU'
            if is_urbanizado_no_edif:
                return 'UNUE'
            return 'UNEU'
        # Comercial, Industrial, Institucional, Servicios, etc. edificado
        return 'UED'

    # Rural puro
    return 'RU'


def to_decimal(val):
    if val is None or val == '':
        return None
    try:
        if isinstance(val, (int, float, Decimal)):
            return Decimal(str(val))
        s = str(val).replace(',', '').replace('$', '').strip()
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return None


def importar(archivo, vigencia=2026, replace=False, data_start_row=8):
    wb = openpyxl.load_workbook(archivo, data_only=True, read_only=True)
    ws = wb.active

    if replace:
        borrados, _ = ContribuyentePredial.objects.filter(vigencia=vigencia).delete()
        print(f'Borrados {borrados} registros previos de vigencia {vigencia}')

    batch = []
    BATCH = 500
    total = 0
    omitidos = 0
    por_cat = {}

    for row in ws.iter_rows(min_row=data_start_row, values_only=True):
        if not row or not row[0]:
            continue
        ref_catastral = str(row[0]).strip()
        if len(row) < 23:
            omitidos += 1
            continue
        propietario = (row[10] or row[2] or '').strip() if isinstance(row[10] or row[2] or '', str) else str(row[10] or row[2] or '').strip()
        direccion = str(row[11] or '').strip()
        tipo = str(row[12] or '').strip()
        destino = str(row[13] or '').strip()
        clase = str(row[14] or '').strip()
        avaluo = to_decimal(row[22])

        if not avaluo or avaluo <= 0:
            omitidos += 1
            continue

        categoria = clasificar(tipo, destino, clase)
        por_cat[categoria] = por_cat.get(categoria, 0) + 1

        batch.append(ContribuyentePredial(
            vigencia=vigencia,
            direccion=direccion[:300] or tipo[:300],
            nombre_predio=(destino or clase or 'PREDIO')[:200],
            propietario=propietario[:300] or 'SIN PROPIETARIO',
            cedula_catastral=ref_catastral[:50],
            avaluo_catastral=avaluo,
            categoria=categoria,
        ))

        if len(batch) >= BATCH:
            ContribuyentePredial.objects.bulk_create(batch, ignore_conflicts=False)
            total += len(batch)
            batch = []
            if total % 2000 == 0:
                print(f'  ... {total} importados')

    if batch:
        ContribuyentePredial.objects.bulk_create(batch, ignore_conflicts=False)
        total += len(batch)

    print(f'\nTotal importados: {total}')
    print(f'Omitidos (sin avalúo): {omitidos}')
    print('Por categoría:')
    for k, v in sorted(por_cat.items(), key=lambda x: -x[1]):
        print(f'  {k}: {v}')
    return total


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Importar predial comparativo a ContribuyentePredial')
    parser.add_argument('archivo', help='Ruta al .xlsx de la tabla predial comparativo')
    parser.add_argument('--vigencia', type=int, default=2026)
    parser.add_argument('--replace', action='store_true', help='Borrar registros previos de esa vigencia')
    parser.add_argument('--start-row', type=int, default=8, help='Fila de inicio de datos (default 8)')
    args = parser.parse_args()
    importar(args.archivo, vigencia=args.vigencia, replace=args.replace, data_start_row=args.start_row)
