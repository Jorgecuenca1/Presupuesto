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
]
