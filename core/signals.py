"""Signals para recálculo automático MFMP.

Al cambiar cualquier variable base (Variables Macro, Parámetros del sistema,
Parámetros anuales), TODO el MFMP se recalcula en cascada automáticamente.
Sin necesidad de botón "recalcular".
"""
import threading
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

# Guard anti-recursión: durante un recálculo, los signals se ignoran
_recalc_flag = threading.local()


def _dentro_de_recalculo():
    return getattr(_recalc_flag, 'activo', False)


def _marcar_recalculando(estado):
    _recalc_flag.activo = estado


def _recalcular_todo():
    """Ejecuta la cascada MFMP completa evitando recursión.

    También aplica un mini-debounce vía cache (evita ejecutar >1 vez/2s
    si múltiples signals dispararon casi simultáneamente durante el mismo
    request).
    """
    if _dentro_de_recalculo():
        return
    # Debounce ligero: si otro request acaba de recalcular hace <2s, saltar
    if cache.get('_mfmp_recalculo_lock'):
        return
    cache.set('_mfmp_recalculo_lock', True, 2)
    try:
        _marcar_recalculando(True)
        from .mfmp_recalculo import recalcular_mfmp
        try:
            recalcular_mfmp()
        except Exception as e:
            # No romper el request principal si el recálculo falla
            import logging
            logging.getLogger(__name__).warning(f'MFMP recalculo error: {e}')
    finally:
        _marcar_recalculando(False)


# ═══ Modelos que disparan recálculo ══════════════════════════════════════

def _instalar_signals():
    """Registra los receivers. Se llama desde apps.ready()."""
    from .models import (
        VariableMacro, ParametrosSistema,
        ParametroAnualPredial, ParametroAnualPlanta, BaseEstampillasAnual,
        ProyeccionRubroIngreso, ProyeccionRubroGasto,
        PlantaDetalleCargo, ICOProyeccion,
    )

    modelos_base = [
        VariableMacro, ParametrosSistema,
        ParametroAnualPredial, ParametroAnualPlanta, BaseEstampillasAnual,
        PlantaDetalleCargo, ICOProyeccion,
    ]

    # Signal para modelos base: al cambiar CUALQUIER campo, se recalcula todo
    def handler(sender, **kwargs):
        _recalcular_todo()

    for M in modelos_base:
        post_save.connect(handler, sender=M, weak=False,
                          dispatch_uid=f'mfmp_recalc_{M.__name__}')
        post_delete.connect(handler, sender=M, weak=False,
                            dispatch_uid=f'mfmp_recalc_del_{M.__name__}')
