"""Middleware de optimización MFMP.

Agrupa múltiples signals dentro de una request en un solo recálculo al
final. Sin este middleware, un import de 1774 contribuyentes dispararía
1774 recálculos completos. Con este middleware: 1 recálculo total.

Fuera de request (script, shell, tests): los signals ejecutan inmediato.
Se detecta con la flag `_local.dentro_request` que solo el middleware setea.
"""
import threading

_local = threading.local()


def dentro_de_request():
    """True solo mientras el middleware está procesando una request web."""
    return getattr(_local, 'dentro_request', False)


def marcar_sucio():
    """Los signals llaman esto para agrupar dentro de una request."""
    _local.sucio = True


def esta_sucio():
    return getattr(_local, 'sucio', False)


def limpiar():
    _local.sucio = False
    _local.dentro_request = False


class RecalculoAgrupadoMiddleware:
    """Al terminar la request, si hubo signals sucios, recalcula 1 sola vez."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _local.dentro_request = True
        _local.sucio = False
        response = self.get_response(request)
        # Si algún signal marcó cambios, recalcular al final e invalidar caché
        if esta_sucio():
            try:
                from django.core.cache import cache
                cache.delete('_mfmp_recalc_reciente')  # invalidar caché perezoso
                from .mfmp_recalculo import recalcular_mfmp
                recalcular_mfmp()
                # Marcar reciente para las próximas vistas de esta ventana de 30s
                cache.set('_mfmp_recalc_reciente', True, 30)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f'Recalc post-request err: {e}')
            finally:
                limpiar()
        return response
