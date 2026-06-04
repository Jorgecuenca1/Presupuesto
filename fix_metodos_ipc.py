"""Reclasifica como IPC los rubros que naturalmente dependen del IPC.

Patron tomado de crear_datos_iniciales.py (diseno original): impuestos menores,
sobretasas, multas, sanciones, intereses moratorios, contribuciones tributarias
y rendimientos financieros se proyectan con la tasa IPC sobre el recaudo del
ano anterior.

Para preservar el valor actual (manual) como linea base, se calcula:
    recaudo_vigencia_anterior = valor_apropiacion / (1 + tasa_ipc)

Asi, al ejecutar calcular_todos_ingresos:
    valor_apropiacion = recaudo_vigencia_anterior * (1 + tasa_ipc)
                      = valor_apropiacion_actual  (sin cambio inmediato)

Y a partir de ese momento, cambiar tasa_ipc en ParametrosSistema + Guardar
ajusta automaticamente todos estos rubros.

Idempotente: si un rubro ya esta en IPC con recaudo coherente, no lo toca.
Nunca borra datos. No toca rubros titulo, predial, ICA, estampillas, POAI,
SGP (que usan ICN), ni transferencias fijas (banca, superavit, reservas).
"""
import os
from decimal import Decimal

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'presupuesto_project.settings')
django.setup()

from ingresos.models import RubroIngreso
from ingresos.utils import calcular_todos_ingresos
from core.models import ParametrosSistema


CODIGOS_IPC = [
    '1.1.01.01.014.01',          # Sobretasa ambiental - Urbano
    '1.1.01.02.109',             # Sobretasa a la gasolina
    '1.1.01.02.202',             # Impuesto a la publicidad exterior visual
    '1.1.01.02.203',             # Impuesto de circulacion y transito
    '1.1.01.02.204',             # Impuesto de delineacion
    '1.1.01.02.211',             # Impuesto de alumbrado publico
    '1.1.01.02.214',             # Impuesto de transporte por oleoductos y gasoductos
    '1.1.02.01.005.64.02',       # Contribucion Sector Electrico
    '1.1.02.01.005.65',          # Concurso Economico - Estratificacion
    '1.1.02.03.001.03',          # Sanciones disciplinarias
    '1.1.02.03.001.06',          # Sanciones Fiscales
    '1.1.02.03.001.09',          # Multas de transito y transporte
    '1.1.02.03.001.11',          # Sanciones tributarias
    '1.1.02.03.002.01',          # Intereses moratorios - Predial
    '1.1.02.03.002.02',          # Intereses moratorios - Industria y Comercio
    '1.1.02.06.006.06.01',       # Cigarrillos nacionales y extranjeros
    '1.3.2.1.1.1.01.02.214',     # Transporte oleoductos/gasoductos (salud)
    '1.3.3.1.1.02.01.005.59',    # Contribucion especial obras publicas (5%)
    '1.3.3.1.1.02.03.001.20.01', # Multas codigo nacional Seguridad y Convivencia
    '1.3.3.1.1.02.03.001.20.02', # Multas codigo nacional Seguridad y Convivencia
    '1.3.5.1.1.01.02.212',       # Sobretasa Bomberil
]


def run():
    p = (ParametrosSistema.objects.filter(activo=True).first()
         or ParametrosSistema.objects.order_by('-vigencia').first())
    if not p:
        print('No hay ParametrosSistema; abortando.')
        return
    v = p.vigencia
    factor = Decimal('1') + p.tasa_ipc
    print(f'Vigencia: {v}   tasa_ipc={p.tasa_ipc} (factor={factor})')

    print('\n== Reclasificando a IPC ==')
    cambios = 0
    saltados = []
    no_encontrados = []
    for cod in CODIGOS_IPC:
        rubros = list(RubroIngreso.objects.filter(vigencia=v, codigo=cod, es_titulo=False))
        if not rubros:
            no_encontrados.append(cod)
            continue
        for r in rubros:
            valor = r.valor_apropiacion or Decimal('0')
            if valor == 0:
                # No hay valor base que preservar; dejamos recaudo=0 (el usuario
                # puede llenarlo manualmente despues). Solo cambiamos metodo.
                if r.metodo_calculo != 'IPC':
                    r.metodo_calculo = 'IPC'
                    r.save(update_fields=['metodo_calculo'])
                    cambios += 1
                    print(f'  {cod} [{r.descripcion[:50]}]  metodo={r.metodo_calculo} (valor=0, recaudo=0)')
                else:
                    saltados.append((cod, 'valor=0 ya IPC'))
                continue
            recaudo_base = (valor / factor).quantize(Decimal('0.01'))
            cambio_metodo = (r.metodo_calculo != 'IPC')
            cambio_recaudo = (r.recaudo_vigencia_anterior != recaudo_base)
            if cambio_metodo or cambio_recaudo:
                r.metodo_calculo = 'IPC'
                r.recaudo_vigencia_anterior = recaudo_base
                r.save(update_fields=['metodo_calculo', 'recaudo_vigencia_anterior'])
                cambios += 1
                print(f'  {cod} [{r.descripcion[:50]}]  '
                      f'valor={valor:,.0f}  recaudo_ant={recaudo_base:,.0f}')
            else:
                saltados.append((cod, 'sin cambios'))

    print(f'\n{cambios} rubros actualizados.')
    if saltados:
        print(f'{len(saltados)} sin cambios (ya configurados).')
    if no_encontrados:
        print(f'\nCodigos no encontrados en DB ({len(no_encontrados)}):')
        for c in no_encontrados:
            print(f'  {c}')

    print('\n== Ejecutando calcular_todos_ingresos ==')
    calcular_todos_ingresos(v)

    print('\n== Verificacion: rubros IPC despues del recalculo ==')
    total = Decimal('0')
    for r in RubroIngreso.objects.filter(vigencia=v, metodo_calculo='IPC').order_by('codigo'):
        print(f'  {r.codigo:30} {r.descripcion[:42]:42}  recaudo_ant={r.recaudo_vigencia_anterior:>15,.0f}  valor={r.valor_apropiacion:>15,.0f}')
        total += r.valor_apropiacion
    print(f'\nTotal rubros IPC: ${total:,.0f}')


if __name__ == '__main__':
    run()
