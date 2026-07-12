from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('registro/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('parametros/', views.parametros_view, name='parametros'),
    path('tabla-concejo/', views.tabla_concejo_personeria, name='tabla_concejo_personeria'),
    path('tabla-concejo/guardar/', views.tabla_concejo_guardar, name='tabla_concejo_guardar'),
    path('tabla-concejo/<int:pk>/eliminar/', views.tabla_concejo_eliminar, name='tabla_concejo_eliminar'),
    path('progresion-smlv/guardar/', views.progresion_smlv_guardar, name='progresion_smlv_guardar'),
    path('progresion-smlv/<int:pk>/eliminar/', views.progresion_smlv_eliminar, name='progresion_smlv_eliminar'),
    path('variables-macro/', views.variables_macro_view, name='variables_macro'),
    path('variables-macro/agregar/', views.variable_macro_agregar, name='variable_macro_agregar'),
    path('variables-macro/<int:pk>/eliminar/', views.variable_macro_eliminar, name='variable_macro_eliminar'),
    path('techos-inversion/', views.techos_inversion_view, name='techos_inversion'),

    # MFMP - Marco Fiscal de Mediano Plazo
    path('mfmp/', views.mfmp_menu, name='mfmp_menu'),
    path('mfmp/plan-financiero/', views.plan_financiero_view, name='plan_financiero'),
    path('mfmp/icld-proyectado/', views.icld_proyectado_view, name='icld_proyectado'),
    path('mfmp/ley-617/', views.ley_617_view, name='ley_617'),
    path('mfmp/poai/', views.poai_proyectado_view, name='poai_proyectado'),
    path('mfmp/poai-dependencias/', views.poai_dependencias_view, name='poai_dependencias'),
    path('mfmp/cuadre-fuente/', views.cuadre_fuente_view, name='cuadre_fuente'),
    path('mfmp/saldo-vf-fuente/', views.saldo_vf_fuente_view, name='saldo_vf_fuente'),
]
