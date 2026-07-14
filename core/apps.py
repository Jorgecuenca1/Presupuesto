from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Registrar signals de recálculo automático MFMP
        try:
            from . import signals
            signals._instalar_signals()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f'MFMP signals no cargados: {e}')
