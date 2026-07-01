"""Context processors para inyectar variables globales en todos los templates."""
from .models import ParametrosSistema
from .constants import BANCOS_COLOMBIA, RENTAS_PIGNORABLES


def vigencia_global(request):
    """Inyecta `vigencia_activa` y `params_global` para uso en base.html
    y otras vistas que no tienen acceso directo al params actual.
    """
    p = ParametrosSistema.objects.filter(activo=True).first()
    return {
        'vigencia_activa': p.vigencia if p else None,
        'params_global': p,
        'bancos_colombia': BANCOS_COLOMBIA,
        'rentas_pignorables': RENTAS_PIGNORABLES,
    }
