"""Restaura los valores originales (preIPC) de los rubros de oleoductos.

Quedaron mal porque entre que los puse en IPC y los revertí a MAN, la tasa_ipc
cambió a 0.10, dejando el valor_apropiacion en el resultado de recaudo×1.10
en vez del recaudo×1.15 que preservaba el valor original.

Restaura los montos exactos que tenían antes de cualquier modificación.
"""
import os
from decimal import Decimal

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'presupuesto_project.settings')
django.setup()

from ingresos.models import RubroIngreso
from ingresos.utils import calcular_todos_ingresos
from core.models import ParametrosSistema


VALORES_ORIGINALES = {
    '1.1.01.02.214': Decimal('14107935272'),          # Oleoductos tributario
    '1.3.2.1.1.1.01.02.214': Decimal('236000000'),    # Oleoductos salud
}


def run():
    p = (ParametrosSistema.objects.filter(activo=True).first()
         or ParametrosSistema.objects.order_by('-vigencia').first())
    v = p.vigencia
    print(f'Vigencia: {v}  tasa_ipc actual={p.tasa_ipc}')

    print('\n== Restaurando valores originales de oleoductos ==')
    for cod, valor in VALORES_ORIGINALES.items():
        for r in RubroIngreso.objects.filter(vigencia=v, codigo=cod, es_titulo=False):
            antes = r.valor_apropiacion
            r.metodo_calculo = 'MAN'
            r.valor_apropiacion = valor
            r.recaudo_vigencia_anterior = Decimal('0')
            r.save(update_fields=['metodo_calculo', 'valor_apropiacion', 'recaudo_vigencia_anterior'])
            print(f'  {cod} [{r.descripcion[:50]}]  {antes:,.0f} -> {valor:,.0f}')

    print('\n== Recalculando titulos ==')
    calcular_todos_ingresos(v)
    print('Listo.')


if __name__ == '__main__':
    run()
