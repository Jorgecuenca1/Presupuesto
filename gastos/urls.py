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

    # Limpiar datos
    path('limpiar/', views.limpiar_gastos, name='limpiar_gastos'),

    # Reporte
    path('reporte/', views.reporte_gastos, name='reporte_gastos'),
    path('reporte/exportar/', views.exportar_gastos_excel, name='exportar_gastos'),
    path('ejecucion/exportar/', views.exportar_ejecucion_excel, name='exportar_ejecucion'),

    # Cifras Históricas Gastos
    path('cifras-historicas/', views.cifras_historicas_gastos, name='cifras_historicas_gastos'),
    path('cifras-historicas/guardar/', views.cifra_historica_gasto_guardar, name='cifra_historica_gasto_guardar'),
    path('cifras-historicas/<int:pk>/eliminar/', views.cifra_historica_gasto_eliminar, name='cifra_historica_gasto_eliminar'),
    path('cifras-historicas/importar/', views.importar_cifras_historicas_gastos, name='importar_cifras_historicas_gastos'),
    path('cifras-historicas/calcular-tcpa/', views.calcular_tcpa_gastos, name='calcular_tcpa_gastos'),

    # Deuda Pública
    path('deuda/', views.deuda_contratos_list, name='servicio_deuda_list'),
    path('deuda/contratos/', views.deuda_contratos_list, name='deuda_contratos_list'),
    path('deuda/contratos/guardar/', views.deuda_contrato_guardar, name='deuda_contrato_guardar'),
    path('deuda/contratos/<int:pk>/eliminar/', views.deuda_contrato_eliminar, name='deuda_contrato_eliminar'),
    path('deuda/contratos/<int:contrato_pk>/pagares/', views.deuda_pagares, name='deuda_pagares'),
    path('deuda/pagares/guardar/', views.deuda_pagare_guardar, name='deuda_pagare_guardar'),
    path('deuda/pagares/<int:pk>/eliminar/', views.deuda_pagare_eliminar, name='deuda_pagare_eliminar'),
    path('deuda/pagares/<int:pagare_pk>/amortizacion/', views.deuda_amortizacion, name='deuda_amortizacion'),
    path('deuda/resumen/', views.deuda_resumen, name='deuda_resumen'),

    # Costo de Personal
    path('personal/', views.costo_personal_list, name='costo_personal_list'),
    path('personal/guardar/', views.costo_personal_guardar, name='costo_personal_guardar'),
    path('personal/<int:pk>/eliminar/', views.costo_personal_eliminar, name='costo_personal_eliminar'),
    path('personal/exportar/', views.exportar_costo_personal, name='exportar_costo_personal'),
    path('personal/importar/', views.importar_costo_personal, name='importar_costo_personal'),

    # Vigencias Futuras
    path('vigencias-futuras/', views.vigencias_futuras_list, name='vigencias_futuras_list'),
    path('vigencias-futuras/guardar/', views.vigencia_futura_guardar, name='vigencia_futura_guardar'),
    path('vigencias-futuras/<int:pk>/eliminar/', views.vigencia_futura_eliminar, name='vigencia_futura_eliminar'),

    # Reporte Techos de Inversión
    path('reporte-techos/', views.reporte_techos_inversion, name='reporte_techos_inversion'),
]
