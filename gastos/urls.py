from django.urls import path
from . import views

urlpatterns = [
    # Secciones
    path('secciones/', views.secciones_list, name='gastos_secciones'),
    path('secciones/guardar/', views.seccion_guardar, name='seccion_guardar'),
    path('secciones/<int:pk>/eliminar/', views.seccion_eliminar, name='seccion_eliminar'),

    # Fuentes
    path('fuentes/', views.fuentes_list, name='gastos_fuentes'),
    path('fuentes/guardar/', views.fuente_guardar, name='fuente_guardar'),
    path('fuentes/<int:pk>/eliminar/', views.fuente_eliminar, name='fuente_eliminar'),

    # Rubros de Gasto
    path('rubros/', views.rubros_gasto_list, name='rubros_gasto_list'),
    path('rubros/crear/', views.rubro_gasto_crear, name='rubro_gasto_crear'),
    path('rubros/<int:pk>/editar/', views.rubro_gasto_editar, name='rubro_gasto_editar'),
    path('rubros/<int:pk>/eliminar/', views.rubro_gasto_eliminar, name='rubro_gasto_eliminar'),

    # Importación
    path('importar-anexo2/', views.importar_anexo2, name='importar_anexo2'),
    path('importar-ejecucion/', views.importar_ejecucion, name='importar_ejecucion'),

    # Ejecución
    path('ejecucion/', views.ejecucion_gastos, name='ejecucion_gastos'),
    path('ejecucion/<int:pk>/editar/', views.ejecucion_editar, name='ejecucion_editar'),

    # Recalcular
    path('recalcular/', views.recalcular_gastos, name='recalcular_gastos'),

    # Reporte
    path('reporte/', views.reporte_gastos, name='reporte_gastos'),
    path('reporte/exportar/', views.exportar_gastos_excel, name='exportar_gastos'),
    path('ejecucion/exportar/', views.exportar_ejecucion_excel, name='exportar_ejecucion'),
]
