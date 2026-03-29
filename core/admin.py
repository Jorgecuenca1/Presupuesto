from django.contrib import admin
from .models import ParametrosSistema


@admin.register(ParametrosSistema)
class ParametrosSistemaAdmin(admin.ModelAdmin):
    list_display = ['vigencia', 'valor_uvt', 'tasa_ipc', 'tasa_icn', 'tasa_pib_nominal', 'activo']
    list_filter = ['activo']
