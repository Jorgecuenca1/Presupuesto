"""Inicializa Anexo 6 - Órganos de Control con datos del Excel.

1. Carga TablaConcejoPersoneria con los valores del Excel "calculo gastos
   organos de control 2026" (7 categorías).
2. Carga PersoneriaSMLVProgresion para 5ª categoría (Ley 2461/2422):
   2025=210, 2026=220, 2027=230, 2028=240, 2029=250.
3. Asigna método OCC al rubro de gasto del Concejo (01.2) y OCP al de
   Personería (02.2) para que se autocalculen.
4. Ejecuta recalcular_rubros_metodo para propagar los valores.

Idempotente: update_or_create. No borra nada.
"""
import os
from decimal import Decimal
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'presupuesto_project.settings')
django.setup()

from core.models import (
    ParametrosSistema, TablaConcejoPersoneria, PersoneriaSMLVProgresion
)
from gastos.models import RubroGasto
from gastos.utils import recalcular_rubros_metodo, calcular_icld


# Excel "calculo gastos organos de control 2026":
# Por categoría: valor_sesion, ses_ord, ses_extra, num_conc, %ICLD personeria,
#                personeria_smlv_fijo
TABLA_CATEGORIAS = [
    # (categoria, valor_sesion, ses_ord, ses_extra, num_conc, pct_pers, smlv_fijo)
    (0, 757771,    150, 40, 19, Decimal('1.6'), 0),    # Especial
    (1, 717999.75, 150, 40, 17, Decimal('1.7'), 0),    # 1ª
    (2, 518983.45, 150, 40, 15, Decimal('2.2'), 0),    # 2ª
    (3, 416306.10,  80, 40, 15, Decimal('0'),   400),  # 3ª (400 SMLV fijos)
    (4, 348256.50,  80, 40, 13, Decimal('0'),   330),  # 4ª (330 SMLV fijos)
    (5, 348256.50,  80, 40, 13, Decimal('0'),   0),    # 5ª (usa progresion)
    (6, 348256.50,  80, 40, 13, Decimal('0'),   0),    # 6ª (0)
]

# Progresion Ley 2461/2422 (Categoría 5)
PROGRESION_CAT5 = [
    (2025, 210),
    (2026, 220),
    (2027, 230),
    (2028, 240),
    (2029, 250),
]


def run():
    p = (ParametrosSistema.objects.filter(activo=True).first()
         or ParametrosSistema.objects.order_by('-vigencia').first())
    if not p:
        print('No hay ParametrosSistema; abortando.')
        return
    v = p.vigencia
    print(f'Vigencia: {v}, categoria municipio: {p.categoria_municipio}')

    # Autollenar ICLD si esta en 0
    if not p.icld_calculado or p.icld_calculado <= 0:
        icld_auto = calcular_icld(v)
        if icld_auto > 0:
            p.icld_calculado = icld_auto
            p.save(update_fields=['icld_calculado'])
            print(f'ICLD autollenado desde Cifras Historicas: ${icld_auto:,.0f}')
        else:
            # Usar el del Excel como fallback
            p.icld_calculado = Decimal('26478285205.13')
            p.save(update_fields=['icld_calculado'])
            print(f'ICLD inicializado con valor del Excel: ${p.icld_calculado:,.0f}')

    print('\n== Cargando TablaConcejoPersoneria ==')
    for cat, vs, so, se, nc, pp, smlvf in TABLA_CATEGORIAS:
        obj, created = TablaConcejoPersoneria.objects.update_or_create(
            categoria=cat,
            defaults={
                'valor_sesion_concejal': Decimal(str(vs)),
                'sesiones_ordinarias': so,
                'sesiones_extraordinarias': se,
                'num_concejales': nc,
                'limite_personeria_pct_icld': pp,
                'personeria_smlv_fijo': smlvf,
            })
        accion = 'creada' if created else 'actualizada'
        print(f'  Cat {cat}: {accion} (valor_sesion={vs}, conc={nc}, pers_pct={pp}%, smlv_fijo={smlvf})')

    print('\n== Cargando Progresion SMLV Personeria (Cat 5) ==')
    for vig, smlv in PROGRESION_CAT5:
        obj, created = PersoneriaSMLVProgresion.objects.update_or_create(
            vigencia=vig, categoria=5,
            defaults={'smlv': smlv})
        accion = 'creada' if created else 'actualizada'
        print(f'  {vig}: {smlv} SMLV ({accion})')

    print('\n== Asignando metodos OCC/OCP a rubros de gasto ==')
    # Concejo: 01.2 SECCION 01 CONCEJO MUNICIPAL
    rubros_concejo = list(RubroGasto.objects.filter(vigencia=v, codigo='01.2'))
    for r in rubros_concejo:
        if r.metodo_calculo != 'OCC':
            r.metodo_calculo = 'OCC'
            r.save(update_fields=['metodo_calculo'])
            print(f'  Concejo: {r.codigo} {r.descripcion[:50]} -> OCC')

    # Personeria: 02.2 SECCION 02 PERSONERIA MUNICIPAL
    rubros_pers = list(RubroGasto.objects.filter(vigencia=v, codigo='02.2'))
    for r in rubros_pers:
        if r.metodo_calculo != 'OCP':
            r.metodo_calculo = 'OCP'
            r.save(update_fields=['metodo_calculo'])
            print(f'  Personería: {r.codigo} {r.descripcion[:50]} -> OCP')

    if not rubros_concejo:
        print('  ⚠ No se encontró rubro 01.2 (Concejo). Verificar carga de gastos.')
    if not rubros_pers:
        print('  ⚠ No se encontró rubro 02.2 (Personería).')

    print('\n== Ejecutando recalcular_rubros_metodo ==')
    resumen = recalcular_rubros_metodo(v)
    print(f'  OCC: {resumen.get("OCC", {})}')
    print(f'  OCP: {resumen.get("OCP", {})}')

    # Verificacion final
    tabla = TablaConcejoPersoneria.objects.get(categoria=p.categoria_municipio)
    transf_c = tabla.calcular_transferencia_concejo(
        p.icld_calculado, p.valor_smlmv, p.pct_icld_adicional_concejo)
    transf_p = tabla.calcular_transferencia_personeria(
        v, p.icld_calculado, p.valor_smlmv)
    print(f'\n== Calculos finales para cat {p.categoria_municipio} vigencia {v} ==')
    print(f'  Total Transferencia Concejo:    ${transf_c:,.0f}')
    print(f'  Total Transferencia Personería: ${transf_p:,.0f}')


if __name__ == '__main__':
    run()
