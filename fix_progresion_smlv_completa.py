"""Corrige la progresion SMLV Personeria para categorias 3, 4, 5 y 6.

Regla Ley 2461/2422: cada categoria sube +10 SMLV por año desde 2024
hasta 2029, luego se estanca en el valor de 2029.

Valores base 2024:
  Cat 3: 400 SMLV
  Cat 4: 330 SMLV
  Cat 5: 210 SMLV
  Cat 6: 200 SMLV

No toca:
  Cat 0/1/2 (Especial/1ª/2ª): usan %ICLD, no SMLV.

Idempotente: update_or_create por (vigencia, categoria).
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'presupuesto_project.settings')
django.setup()

from core.models import (
    PersoneriaSMLVProgresion, ParametrosSistema, TablaConcejoPersoneria,
)

BASE_2024 = {3: 400, 4: 330, 5: 210, 6: 200}
PROGRESION_HASTA = 2029
TOPE_VIGENCIA = 2035  # rellenar hasta este año con el valor de 2029


def smlv_para(cat, vigencia):
    """Devuelve el SMLV de Personeria para una categoria y vigencia."""
    base = BASE_2024.get(cat)
    if base is None:
        return None
    if vigencia < 2024:
        return base
    if vigencia >= PROGRESION_HASTA:
        return base + (PROGRESION_HASTA - 2024) * 10
    return base + (vigencia - 2024) * 10


def run():
    print('========== ANTES ==========')
    for pr in PersoneriaSMLVProgresion.objects.all().order_by('categoria', 'vigencia'):
        print(f'  cat={pr.categoria}  vig={pr.vigencia}  smlv={pr.smlv}')

    print('\n========== APLICANDO PROGRESION ==========')
    cambios = 0
    creados = 0
    for cat, base in BASE_2024.items():
        for vig in range(2024, TOPE_VIGENCIA + 1):
            smlv = smlv_para(cat, vig)
            obj, created = PersoneriaSMLVProgresion.objects.update_or_create(
                vigencia=vig, categoria=cat,
                defaults={'smlv': smlv})
            if created:
                creados += 1
            else:
                cambios += 1
    print(f'  Filas creadas: {creados}, actualizadas: {cambios}')

    print('\n========== DESPUES (resumen 2024-2029) ==========')
    for cat in sorted(BASE_2024.keys()):
        valores = []
        for vig in range(2024, 2030):
            pr = PersoneriaSMLVProgresion.objects.filter(vigencia=vig, categoria=cat).first()
            valores.append(f'{vig}={pr.smlv if pr else "-"}')
        print(f'  Cat {cat}:  ' + '  '.join(valores))

    p = ParametrosSistema.objects.filter(activo=True).first()
    if p:
        print(f'\n========== IMPACTO EN MUNICIPIO ACTUAL ==========')
        print(f'Vigencia activa: {p.vigencia}, Categoria: {p.categoria_municipio}, SMLMV: ${p.valor_smlmv:,.0f}')
        tabla = TablaConcejoPersoneria.objects.filter(categoria=p.categoria_municipio).first()
        if tabla:
            tp_antes = None  # no podemos calcular el anterior, ya se sobreescribio
            tp_nuevo = tabla.calcular_transferencia_personeria(
                p.vigencia, p.icld_calculado, p.valor_smlmv)
            print(f'Personeria (NUEVO con progresion corregida): ${tp_nuevo:,.0f}')

        # Recalcular todo
        from ingresos.utils import calcular_todos_ingresos
        from gastos.utils import recalcular_rubros_metodo
        from ingresos.models import RubroIngreso
        from gastos.models import RubroGasto
        calcular_todos_ingresos(p.vigencia)
        resumen = recalcular_rubros_metodo(p.vigencia)
        for t in RubroIngreso.objects.filter(vigencia=p.vigencia, es_titulo=True).order_by('-nivel'):
            t.calcular_hijos()
        for t in RubroGasto.objects.filter(vigencia=p.vigencia, es_titulo=True).order_by('-nivel'):
            t.calcular_hijos()
        print(f'\nRubros recalculados:')
        for m, info in resumen.items():
            if info['rubros']:
                print(f'  {m}: {info["rubros"]} rubros, ${info["total_aplicado"]:,.0f}')


if __name__ == '__main__':
    run()
