"""Reclasifica los ContribuyentePredial aplicando la regla correcta:
  - Parcelaciones/Fincas de recreo → PE / PNE (rural)
  - CABECERA MUNICIPAL → urbano (UV, UED, UEF, UNEU, UNUE, UNNU)
  - Cualquier otro tipo (RURAL o corregimientos) → RU

El criterio rural/urbano se deriva del campo 'direccion' (que fue poblado desde el TIPO
del Excel) y el 'nombre_predio' (que fue poblado desde DESTINO).
No elimina registros; solo actualiza la columna 'categoria'.
"""
import argparse
import os
import sys

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'presupuesto_project.settings')
django.setup()

from ingresos.models import ContribuyentePredial


URBANO_TIPOS = {
    # SOLO cabecera municipal cuenta como urbano
    'CABECERA MUNICIPAL',
}


def reclasificar_uno(direccion, nombre_predio, cat_actual):
    """Retorna la nueva categoria correcta según direccion (=tipo) y nombre_predio (=destino).
    Si los campos no tienen señal clara, mantiene la categoria actual."""
    d = (direccion or '').upper()
    dest = (nombre_predio or '').upper()

    # Parcelaciones/Fincas: siempre rurales
    if cat_actual in ('PE', 'PNE'):
        return cat_actual

    # Si el direccion empieza con un tipo rural/corregimiento → RU
    es_cabecera = 'CABECERA MUNICIPAL' in d[:30]

    if not es_cabecera:
        # Cualquier corregimiento o RURAL → RU (excepto parcelaciones que ya devolvimos)
        return 'RU'

    # Es cabecera → determinar sub-categoría urbana por destino
    if 'FINANCIERA' in dest:
        return 'UEF'
    if 'HABITACIONAL' in dest:
        return 'UV'
    if 'LOTE' in dest:
        if 'NO URBANIZABLE' in dest:
            return 'UNNU'
        if 'URBANIZABLE NO URBAN' in dest:
            return 'UNEU'
        if 'URBANIZADO NO CONST' in dest:
            return 'UNUE'
        return 'UNEU'
    # Comercial, industrial, institucional, etc.
    return 'UED'


def run(vigencia=2026, dry_run=False):
    cambios = {}
    total_actual = {}
    total_nuevo = {}
    qs = ContribuyentePredial.objects.filter(vigencia=vigencia)
    print(f'Total registros vigencia {vigencia}: {qs.count()}')

    updates = []
    for c in qs.iterator(chunk_size=500):
        nueva = reclasificar_uno(c.direccion, c.nombre_predio, c.categoria)
        total_actual[c.categoria] = total_actual.get(c.categoria, 0) + 1
        total_nuevo[nueva] = total_nuevo.get(nueva, 0) + 1
        if nueva != c.categoria:
            cambios[(c.categoria, nueva)] = cambios.get((c.categoria, nueva), 0) + 1
            if not dry_run:
                c.categoria = nueva
                updates.append(c)
                if len(updates) >= 500:
                    ContribuyentePredial.objects.bulk_update(updates, ['categoria'])
                    updates = []
    if updates and not dry_run:
        ContribuyentePredial.objects.bulk_update(updates, ['categoria'])

    print('\n== ANTES ==')
    for k, v in sorted(total_actual.items()):
        print(f'  {k}: {v}')
    print('\n== DESPUÉS ==')
    for k, v in sorted(total_nuevo.items()):
        print(f'  {k}: {v}')
    print('\n== Reclasificaciones ==')
    for (a, b), n in sorted(cambios.items(), key=lambda x: -x[1]):
        print(f'  {a} → {b}: {n}')

    URB = {'UV', 'UED', 'UEF', 'UNEU', 'UNUE', 'UNNU'}
    urb = sum(v for k, v in total_nuevo.items() if k in URB)
    rur = sum(v for k, v in total_nuevo.items() if k not in URB)
    print(f'\nTotal URBANO: {urb}')
    print(f'Total RURAL:  {rur}')
    if dry_run:
        print('\n(DRY-RUN: no se guardó nada)')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--vigencia', type=int, default=2026)
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()
    run(args.vigencia, args.dry_run)
