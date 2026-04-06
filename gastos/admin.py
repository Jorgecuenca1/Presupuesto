from django.contrib import admin
from .models import SeccionGasto, FuenteFinanciacion, RubroGasto, EjecucionGasto


@admin.register(SeccionGasto)
class SeccionGastoAdmin(admin.ModelAdmin):
    list_display = ['vigencia', 'codigo', 'nombre']
    list_filter = ['vigencia']


@admin.register(FuenteFinanciacion)
class FuenteFinanciacionAdmin(admin.ModelAdmin):
    list_display = ['vigencia', 'codigo', 'nombre']
    list_filter = ['vigencia']


@admin.register(RubroGasto)
class RubroGastoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'descripcion', 'tipo_gasto', 'valor_apropiacion', 'es_titulo']
    list_filter = ['vigencia', 'tipo_gasto', 'es_titulo']
    search_fields = ['codigo', 'descripcion']


@admin.register(EjecucionGasto)
class EjecucionGastoAdmin(admin.ModelAdmin):
    list_display = ['rubro', 'presupuesto_aprobado', 'compromisos', 'pagado']
    list_filter = ['rubro__vigencia']
    search_fields = ['rubro__codigo', 'rubro__descripcion']
