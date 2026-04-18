"""Completa los predios que quedaron sin avalúo en vigencia actual usando el avalúo anterior.

Se usa sobre el mismo archivo que import_predial.py. No borra nada: solo inserta los
registros cuya cedula_catastral aún no exista para la vigencia objetivo.
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
from import_predial import clasificar, to_decimal


def run(archivo, vigencia=2026):
    wb = openpyxl.load_workbook(archivo, data_only=True, read_only=True)
    ws = wb.active
    existentes = set(ContribuyentePredial.objects
                     .filter(vigencia=vigencia)
                     .values_list('cedula_catastral', flat=True))
    print(f'Ya en DB (vigencia {vigencia}): {len(existentes)} registros')

    nuevos = []
    for row in ws.iter_rows(min_row=8, values_only=True):
        if not row or not row[0]:
            continue
        if len(row) < 23:
            continue
        ref = str(row[0]).strip()[:50]
        if ref in existentes:
            continue
        avaluo = to_decimal(row[22])
        if not avaluo or avaluo <= 0:
            avaluo = to_decimal(row[19])  # columna 20: avalúo vigencia anterior
        if not avaluo or avaluo <= 0:
            print(f'  ! sin avalúo en ninguna vigencia: {ref}')
            continue
        propietario = str(row[10] or row[2] or '').strip()[:300] or 'SIN PROPIETARIO'
        direccion = str(row[11] or '').strip()[:300]
        tipo = str(row[12] or '').strip()
        destino = str(row[13] or '').strip()
        clase = str(row[14] or '').strip()
        categoria = clasificar(tipo, destino, clase)
        nuevos.append(ContribuyentePredial(
            vigencia=vigencia,
            direccion=direccion or tipo[:300],
            nombre_predio=(destino or clase or 'PREDIO')[:200],
            propietario=propietario,
            cedula_catastral=ref,
            avaluo_catastral=avaluo,
            categoria=categoria,
        ))
    if nuevos:
        ContribuyentePredial.objects.bulk_create(nuevos)
    print(f'Insertados {len(nuevos)} registros faltantes')
    print('Total vigencia', vigencia, ':', ContribuyentePredial.objects.filter(vigencia=vigencia).count())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('archivo')
    parser.add_argument('--vigencia', type=int, default=2026)
    args = parser.parse_args()
    run(args.archivo, args.vigencia)
