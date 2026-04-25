from django.urls import path
from . import views

urlpatterns = [
    # Tarifas Predial
    path('tarifas-predial/', views.tarifas_predial, name='tarifas_predial'),
    path('tarifas-predial/guardar/', views.tarifa_predial_guardar, name='tarifa_predial_guardar'),
    path('tarifas-predial/<int:pk>/eliminar/', views.tarifa_predial_eliminar, name='tarifa_predial_eliminar'),
    path('cultura-pago/guardar/', views.cultura_pago_guardar, name='cultura_pago_guardar'),

    # Contribuyentes Predial
    path('contribuyentes-predial/', views.contribuyentes_predial, name='contribuyentes_predial'),
    path('contribuyentes-predial/crear/', views.contribuyente_predial_crear, name='contribuyente_predial_crear'),
    path('contribuyentes-predial/<int:pk>/eliminar/', views.contribuyente_predial_eliminar, name='contribuyente_predial_eliminar'),
    path('importar-predial/', views.importar_predial, name='importar_predial'),

    # Cálculo Predial
    path('calculo-predial/', views.calculo_predial, name='calculo_predial'),
    path('cartera/guardar/', views.cartera_guardar, name='cartera_guardar'),
    path('cartera/<int:pk>/eliminar/', views.cartera_eliminar, name='cartera_eliminar'),

    # Tarifas ICA
    path('tarifas-ica/', views.tarifas_ica, name='tarifas_ica'),
    path('tarifas-ica/guardar/', views.tarifa_ica_guardar, name='tarifa_ica_guardar'),
    path('tarifas-ica/<int:pk>/eliminar/', views.tarifa_ica_eliminar, name='tarifa_ica_eliminar'),

    # Contribuyentes ICA
    path('contribuyentes-ica/', views.contribuyentes_ica, name='contribuyentes_ica'),
    path('contribuyentes-ica/crear/', views.contribuyente_ica_crear, name='contribuyente_ica_crear'),
    path('contribuyentes-ica/<int:pk>/eliminar/', views.contribuyente_ica_eliminar, name='contribuyente_ica_eliminar'),
    path('importar-ica/', views.importar_ica, name='importar_ica'),

    # Cálculo ICA
    path('calculo-ica/', views.calculo_ica, name='calculo_ica'),

    # Estampillas
    path('estampillas/', views.calculo_estampillas, name='calculo_estampillas'),
    path('estampillas/guardar/', views.estampilla_guardar, name='estampilla_guardar'),
    path('estampillas/<int:pk>/eliminar/', views.estampilla_eliminar, name='estampilla_eliminar'),

    # Rubros de Ingreso
    path('rubros/', views.rubros_list, name='rubros_list'),
    path('rubros/crear/', views.rubro_crear, name='rubro_crear'),
    path('rubros/<int:pk>/editar/', views.rubro_editar, name='rubro_editar'),
    path('rubros/<int:pk>/eliminar/', views.rubro_eliminar, name='rubro_eliminar'),

    # Calcular Todos
    path('calcular-todos/', views.calcular_todos, name='calcular_todos'),

    # Reporte
    path('reporte/', views.reporte_ingresos, name='reporte_ingresos'),
    path('reporte/exportar/', views.exportar_reporte_excel, name='exportar_reporte'),

    # Cifras Históricas Ingresos
    path('cifras-historicas/', views.cifras_historicas_ingresos, name='cifras_historicas_ingresos'),
    path('cifras-historicas/guardar/', views.cifra_historica_ingreso_guardar, name='cifra_historica_ingreso_guardar'),
    path('cifras-historicas/<int:pk>/eliminar/', views.cifra_historica_ingreso_eliminar, name='cifra_historica_ingreso_eliminar'),
    path('cifras-historicas/importar/', views.importar_cifras_historicas_ingresos, name='importar_cifras_historicas_ingresos'),
    path('cifras-historicas/calcular-tcpa/', views.calcular_tcpa_ingresos, name='calcular_tcpa_ingresos'),
]
