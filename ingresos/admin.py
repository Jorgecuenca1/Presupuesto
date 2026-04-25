from django.contrib import admin
from .models import (
    TarifaPredial, CulturaPago, ContribuyentePredial, CarteraVigenciaAnterior,
    TarifaICA, ContribuyenteICA, RubroIngreso, ResumenCalculo, Estampilla,
)


@admin.register(Estampilla)
class EstampillaAdmin(admin.ModelAdmin):
    list_display = ['vigencia', 'nombre', 'codigo_rubro', 'tarifa']
    list_filter = ['vigencia']
    search_fields = ['nombre', 'codigo_rubro']


@admin.register(TarifaPredial)
class TarifaPredialAdmin(admin.ModelAdmin):
    list_display = ['vigencia', 'categoria', 'uvt_desde', 'uvt_hasta', 'tarifa_por_mil']
    list_filter = ['vigencia', 'categoria']


@admin.register(CulturaPago)
class CulturaPagoAdmin(admin.ModelAdmin):
    list_display = ['vigencia', 'categoria', 'porcentaje']
    list_filter = ['vigencia']


@admin.register(ContribuyentePredial)
class ContribuyentePredialAdmin(admin.ModelAdmin):
    list_display = ['propietario', 'nombre_predio', 'avaluo_catastral', 'categoria', 'impuesto_calculado']
    list_filter = ['vigencia', 'categoria']
    search_fields = ['propietario', 'nombre_predio']


@admin.register(CarteraVigenciaAnterior)
class CarteraAdmin(admin.ModelAdmin):
    list_display = ['vigencia_calculo', 'vigencia_cartera', 'valor_cartera']


@admin.register(TarifaICA)
class TarifaICAAdmin(admin.ModelAdmin):
    list_display = ['vigencia', 'codigo_actividad', 'tarifa_por_mil']
    list_filter = ['vigencia']


@admin.register(ContribuyenteICA)
class ContribuyenteICAAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'nit', 'actividad', 'ingresos_brutos', 'impuesto_calculado']
    list_filter = ['vigencia', 'actividad']
    search_fields = ['nombre', 'nit']


@admin.register(RubroIngreso)
class RubroIngresoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'descripcion', 'metodo_calculo', 'valor_apropiacion', 'es_titulo']
    list_filter = ['vigencia', 'metodo_calculo', 'es_titulo']
    search_fields = ['codigo', 'descripcion']


@admin.register(ResumenCalculo)
class ResumenCalculoAdmin(admin.ModelAdmin):
    list_display = ['tipo', 'categoria', 'proyeccion', 'fecha_calculo']
    list_filter = ['vigencia', 'tipo']
