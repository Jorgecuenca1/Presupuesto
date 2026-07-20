"""Signals para recálculo automático MFMP end-to-end.

Al modificar CUALQUIER variable, parámetro, tarifa, contribuyente, rubro,
contrato o dato base del sistema, se dispara automáticamente:

  1. `recalcular_mfmp()` - motor MFMP (Plan Financiero, ICLD, Ley 617, POAI,
     Techos, Cuadre, proyecciones, etc.)
  2. `calcular_todos_ingresos()` - Predial, ICA, Estampillas, IPC, POAI base
  3. `_sincronizar_techos_desde_fuentes()` - integración cruzada Techos

El recálculo es SÍNCRONO (dentro de la misma request) para que cualquier
vista subsecuente vea el estado consistente. Sin debounce/lock: mejor
recalcular varias veces que dejar vistas desactualizadas.
"""
import threading
from django.db.models.signals import post_save, post_delete
from django.db import transaction

# Guard anti-recursión: durante un recálculo, los signals se ignoran
_recalc_flag = threading.local()


def _dentro_de_recalculo():
    return getattr(_recalc_flag, 'activo', False)


def _recalcular_todo():
    """Marca la request como "sucia" para que el middleware ejecute UN solo
    recálculo al final. Optimización clave: 1774 saves durante un import
    → 1 recálculo (no 1774).

    Si no hay middleware activo (script suelto, shell), ejecuta inmediato.
    """
    if _dentro_de_recalculo():
        return

    # Modo optimizado: SI hay una request web activa, solo marcar dirty
    # para que el middleware recalcule 1 vez al final.
    try:
        from . import middleware
        if middleware.dentro_de_request():
            middleware.marcar_sucio()
            return
    except Exception:
        pass

    # Fuera de request (shell, tests, scripts, import CLI): ejecutar inmediato
    def _run():
        if _dentro_de_recalculo():
            return
        _recalc_flag.activo = True
        try:
            # 1) MFMP: proyecciones + planes + ICLD + Ley 617 + Techos + POAI
            try:
                from .mfmp_recalculo import recalcular_mfmp
                recalcular_mfmp()
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f'MFMP recalc err: {e}')

            # 2) Ingresos legacy (Predial, ICA, Estampillas, etc.)
            try:
                from .models import ParametrosSistema
                p = ParametrosSistema.objects.filter(activo=True).first()
                if p:
                    from ingresos.utils import calcular_todos_ingresos
                    calcular_todos_ingresos(p.vigencia)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f'Ingresos recalc err: {e}')

            # 3) Techos de Inversión (integración cruzada)
            try:
                from .models import ParametrosSistema
                p = ParametrosSistema.objects.filter(activo=True).first()
                if p:
                    from .views import _sincronizar_techos_desde_fuentes
                    _sincronizar_techos_desde_fuentes(p.vigencia)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f'Techos recalc err: {e}')

            # 4) Deuda pública → propagar a rubros 2.2.x
            try:
                from .models import ParametrosSistema
                from gastos.models import ContratoCredito
                from gastos.views import (_recalcular_amortizacion_contrato,
                                          _propagar_deuda_a_rubros)
                p = ParametrosSistema.objects.filter(activo=True).first()
                if p:
                    for c in ContratoCredito.objects.all():
                        _recalcular_amortizacion_contrato(c)
                    _propagar_deuda_a_rubros(p.vigencia)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f'Deuda recalc err: {e}')

            # 5) Título CUIPO padres
            try:
                from .models import ParametrosSistema
                from .views import _recalcular_titulos_por_codigo
                p = ParametrosSistema.objects.filter(activo=True).first()
                if p:
                    _recalcular_titulos_por_codigo(p.vigencia)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f'Titulos recalc err: {e}')
        finally:
            _recalc_flag.activo = False

    # Ejecutar SIEMPRE. Si estamos en una transacción explícita, esperar
    # al commit. Si no, ejecutar inmediato (caso típico: script suelto,
    # save() individual desde admin/form).
    try:
        from django.db import connection
        if connection.in_atomic_block:
            transaction.on_commit(_run)
        else:
            _run()
    except Exception:
        _run()


# ═══ Modelos que disparan recálculo ══════════════════════════════════════

def _instalar_signals():
    """Registra receivers para TODOS los modelos base del sistema.
    Se llama desde apps.ready().
    """
    from .models import (
        VariableMacro, ParametrosSistema, TablaConcejoPersoneria,
        ParametroAnualPredial, ParametroAnualPlanta, BaseEstampillasAnual,
        ProyeccionRubroIngreso, ProyeccionRubroGasto,
        PlantaDetalleCargo, ICOProyeccion, PersoneriaSMLVProgresion,
        TechoInversion, PlanFinancieroLinea, ICLDProyectado,
        Ley617Proyectado, POAIProyectado, POAIPorDependencia,
        CuadrePorFuente, SaldoVFPorFuente, Refinanciacion,
        FuenteFinanciacion, VigenciaFutura, EjecucionMensualIngreso,
        VigenciaFuturaAprobada,
    )
    from ingresos.models import (
        RubroIngreso, ContribuyenteICA, ContribuyentePredial,
        TarifaICA, Estampilla,
    )
    from gastos.models import (
        RubroGasto, CostoPersonal, ContratoCredito, PagareCredito,
    )

    # Modelos que al cambiar disparan recálculo completo
    modelos_criticos = [
        # Core: parametros globales del sistema
        VariableMacro, ParametrosSistema, TablaConcejoPersoneria,
        PersoneriaSMLVProgresion,
        # MFMP - parametros anuales
        ParametroAnualPredial, ParametroAnualPlanta, BaseEstampillasAnual,
        # MFMP - datos base
        PlantaDetalleCargo, ICOProyeccion, ProyeccionRubroIngreso,
        ProyeccionRubroGasto, FuenteFinanciacion, Refinanciacion,
        EjecucionMensualIngreso, VigenciaFuturaAprobada,
        # Ingresos - reglas de calculo
        TarifaICA, Estampilla,
        # Ingresos - contribuyentes (afecta ICA/Predial)
        ContribuyenteICA, ContribuyentePredial,
        # Gastos - deuda y personal
        CostoPersonal, ContratoCredito, PagareCredito, VigenciaFutura,
    ]

    def handler(sender, **kwargs):
        _recalcular_todo()

    for M in modelos_criticos:
        post_save.connect(handler, sender=M, weak=False,
                          dispatch_uid=f'mfmp_recalc_{M.__name__}')
        post_delete.connect(handler, sender=M, weak=False,
                            dispatch_uid=f'mfmp_recalc_del_{M.__name__}')

    # Rubros: solo notificar en cambios manuales importantes (no en cascadas
    # internas del propio recalculo, gracias al guard _recalc_flag)
    for M in [RubroIngreso, RubroGasto]:
        post_save.connect(handler, sender=M, weak=False,
                          dispatch_uid=f'mfmp_recalc_{M.__name__}')
