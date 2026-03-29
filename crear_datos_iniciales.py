"""
Script para crear datos iniciales del sistema SIPRE.
Incluye: usuario ejemplo, parámetros, tarifas del estatuto tributario,
cultura de pago, contribuyentes ejemplo, carteras y rubros del Anexo 1.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'presupuesto_project.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from decimal import Decimal
from django.contrib.auth.models import User
from core.models import ParametrosSistema
from ingresos.models import (
    TarifaPredial, CulturaPago, ContribuyentePredial, CarteraVigenciaAnterior,
    TarifaICA, ContribuyenteICA, RubroIngreso,
)

VIG = 2026


def crear_usuario():
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@puertolpez.gov.co', 'admin123',
                                      first_name='Administrador', last_name='SIPRE')
        print('Usuario creado: admin / admin123')
    if not User.objects.filter(username='presupuesto').exists():
        u = User.objects.create_user('presupuesto', 'presupuesto@puertolopez.gov.co', 'Puerto2026',
                                     first_name='Secretaría', last_name='de Hacienda')
        u.is_staff = True
        u.save()
        print('Usuario creado: presupuesto / Puerto2026')


def crear_parametros():
    p, created = ParametrosSistema.objects.update_or_create(
        vigencia=VIG,
        defaults={
            'valor_uvt': Decimal('52374'),
            'tasa_ipc': Decimal('0.051'),
            'tasa_icn': Decimal('0.08'),
            'tasa_pib_nominal': Decimal('0.062'),
            'poai_total_inversion': Decimal('50000000000'),
            'activo': True,
        }
    )
    print(f'Parámetros {"creados" if created else "actualizados"} para vigencia {VIG}')


def crear_tarifas_predial():
    TarifaPredial.objects.filter(vigencia=VIG).delete()
    tarifas = [
        # Urbano Vivienda (UVT-based) - Art. 22 Estatuto
        ('UV', 0, 640, 4, 'Predios urbanos vivienda 0-640 UVT'),
        ('UV', 641, 1665, 5, 'Predios urbanos vivienda 641-1665 UVT'),
        ('UV', 1666, 2560, 6, 'Predios urbanos vivienda 1666-2560 UVT'),
        ('UV', 2561, None, 7, 'Predios urbanos vivienda >2560 UVT'),
        # Urbano Edificado Financiero
        ('UEF', None, None, 16, 'Predios actividades financieras'),
        # Urbano Edificado Demás
        ('UED', None, None, 9, 'Demás predios urbanos edificados'),
        # Urbano No Edificado Urbanizable No Urbanizado
        ('UNEU', None, None, 33, 'Lotes urbanizables no urbanizados'),
        # Urbano No Edificado Urbanizado No Edificado
        ('UNUE', None, None, 33, 'Lotes urbanizados no edificados'),
        # Urbano No Edificado No Urbanizable
        ('UNNU', None, None, 6, 'Lotes no urbanizables'),
        # Rural (UVT-based)
        ('RU', 0, 3450, 5, 'Predios rurales 0-3450 UVT'),
        ('RU', 3451, None, 7, 'Predios rurales >3450 UVT'),
        # Parcelaciones Edificadas
        ('PE', None, None, 8, 'Parcelaciones/fincas recreo edificados'),
        # Parcelaciones No Edificadas
        ('PNE', None, None, 13, 'Parcelaciones/fincas recreo no edificados'),
    ]
    for cat, uvt_desde, uvt_hasta, tarifa, desc in tarifas:
        TarifaPredial.objects.create(
            vigencia=VIG, categoria=cat,
            uvt_desde=Decimal(str(uvt_desde)) if uvt_desde is not None else None,
            uvt_hasta=Decimal(str(uvt_hasta)) if uvt_hasta is not None else None,
            tarifa_por_mil=Decimal(str(tarifa)),
            descripcion=desc,
        )
    print(f'{len(tarifas)} tarifas predial creadas')


def crear_cultura_pago():
    CulturaPago.objects.filter(vigencia=VIG).delete()
    culturas = [
        ('UV', 68), ('UEF', 70), ('UED', 68),
        ('UNEU', 70), ('UNUE', 70), ('UNNU', 70),
        ('RU', 40), ('PE', 40), ('PNE', 40),
    ]
    for cat, pct in culturas:
        CulturaPago.objects.create(vigencia=VIG, categoria=cat, porcentaje=Decimal(str(pct)))
    print(f'{len(culturas)} culturas de pago creadas')


def crear_contribuyentes_predial_ejemplo():
    ContribuyentePredial.objects.filter(vigencia=VIG).delete()
    contribuyentes = [
        # Urbano Vivienda
        ('Cra 5 #10-20', 'Casa Centro', 'Juan Pérez López', 25000000, 'UV'),
        ('Cll 8 #15-30', 'Apto Brisas', 'María García Ruiz', 45000000, 'UV'),
        ('Cra 12 #20-10', 'Casa Campestre', 'Carlos Rodríguez', 95000000, 'UV'),
        ('Cll 3 #8-15', 'Residencia Los Pinos', 'Ana Martínez', 150000000, 'UV'),
        ('Cra 7 #5-60', 'Casa Familiar', 'Pedro Sánchez', 15000000, 'UV'),
        ('Cll 15 #22-40', 'Apto Mirador', 'Laura Gómez', 60000000, 'UV'),
        ('Cra 9 #12-80', 'Casa Colonial', 'Roberto López', 200000000, 'UV'),
        # Urbano Edificado Financiero
        ('Cra 5 #8-10', 'Oficina Banco Agrario', 'Banco Agrario', 800000000, 'UEF'),
        ('Cll 10 #5-20', 'Sucursal Bancolombia', 'Bancolombia SA', 650000000, 'UEF'),
        # Urbano Edificado Demás
        ('Cra 6 #9-30', 'Local Comercial Centro', 'Almacenes López', 120000000, 'UED'),
        ('Cll 12 #7-15', 'Bodega Industrial', 'Distribuidora Llano', 300000000, 'UED'),
        ('Cra 8 #11-50', 'Hotel Puerto López', 'Inversiones Turísticas', 500000000, 'UED'),
        # Urbano No Edificado
        ('Cra 15 #25-00', 'Lote Urbanizable', 'Constructora Llano SA', 180000000, 'UNEU'),
        ('Cll 20 #30-00', 'Lote Esquinero', 'Inversiones Meta SAS', 250000000, 'UNEU'),
        # Rural
        ('Vda El Tigre', 'Finca El Porvenir', 'Hernán Castillo', 80000000, 'RU'),
        ('Vda La Balsa', 'Hacienda Los Llanos', 'Agropecuaria Meta', 500000000, 'RU'),
        ('Vda Remolinos', 'Finca La Esperanza', 'José Ramírez', 150000000, 'RU'),
        ('Vda Puerto Porfia', 'Finca El Triunfo', 'Ganadera Oriental', 300000000, 'RU'),
        ('Vda Caño Chiquito', 'Hato Santa Rosa', 'Inversiones Ganaderas', 1200000000, 'RU'),
        # Parcelaciones
        ('Km 5 Vía Restrepo', 'Condominio Los Arrayanes', 'Fernando Díaz', 350000000, 'PE'),
        ('Km 3 Vía Villavicencio', 'Finca Recreo El Paraíso', 'Gloria Suárez', 280000000, 'PE'),
        ('Km 8 Vía Restrepo', 'Lote Campestre Sin Construir', 'Jaime Torres', 200000000, 'PNE'),
    ]
    for dir, nombre, prop, avaluo, cat in contribuyentes:
        ContribuyentePredial.objects.create(
            vigencia=VIG, direccion=dir, nombre_predio=nombre,
            propietario=prop, avaluo_catastral=Decimal(str(avaluo)),
            categoria=cat,
        )
    print(f'{len(contribuyentes)} contribuyentes predial ejemplo creados')


def crear_carteras():
    CarteraVigenciaAnterior.objects.filter(vigencia_calculo=VIG).delete()
    carteras = [
        (2025, 4787816519),
        (2024, 3548629785),
        (2023, 2953533195),
        (2022, 2795207978),
        (2021, 2440904991),
    ]
    for vig, valor in carteras:
        CarteraVigenciaAnterior.objects.create(
            vigencia_calculo=VIG, vigencia_cartera=vig,
            valor_cartera=Decimal(str(valor)),
            porcentaje_base=Decimal('40'), porcentaje_urbano=Decimal('10'),
            porcentaje_rural=Decimal('90'),
        )
    print(f'{len(carteras)} carteras vigencias anteriores creadas')


def crear_tarifas_ica():
    TarifaICA.objects.filter(vigencia=VIG).delete()
    tarifas = [
        ('101', 7, 'Actividad Industrial'),
        ('201', 6, 'Comercio alimentos, víveres, insumos agrícolas'),
        ('202', 8, 'Comercio equipos computación, venta móvil'),
        ('203', 10, 'Comercio lubricantes, combustibles, licores'),
        ('204', 7, 'Otras actividades comerciales'),
        ('301', 10, 'Servicios construcción, transporte, telecom'),
        ('302', 8, 'Otras actividades de servicios'),
        ('401', 5, 'Entidades financieras'),
    ]
    for codigo, tarifa, desc in tarifas:
        TarifaICA.objects.create(
            vigencia=VIG, codigo_actividad=codigo,
            tarifa_por_mil=Decimal(str(tarifa)), descripcion=desc,
        )
    print(f'{len(tarifas)} tarifas ICA creadas')


def crear_contribuyentes_ica_ejemplo():
    ContribuyenteICA.objects.filter(vigencia=VIG).delete()
    contribuyentes = [
        # Industrial
        ('Arroz del Llano SAS', '800100200-1', '101', 1200000000),
        ('Procesadora de Palma Meta', '900200300-5', '101', 800000000),
        # Comercial
        ('Tiendas D1 Puerto López', '900500600-3', '203', 3500000000),
        ('Almacén Agropecuario El Llano', '800300400-2', '201', 500000000),
        ('Distribuidora de Cervezas Meta', '800400500-7', '203', 1500000000),
        ('Compucentro Puerto López', '900100200-4', '202', 300000000),
        ('Supermercado El Económico', '800600700-9', '204', 800000000),
        # Servicios
        ('Bioenergy SAS', '900300400-6', '301', 1200000000),
        ('Transportes del Llano', '800700800-1', '301', 600000000),
        ('Constructora Llanos SAS', '900400500-8', '301', 900000000),
        ('Claro Telecomunicaciones', '800800900-3', '302', 400000000),
        # Financiera
        ('Banco Agrario - Puerto López', '800900100-5', '401', 2000000000),
    ]
    for nombre, nit, act, ingresos in contribuyentes:
        ContribuyenteICA.objects.create(
            vigencia=VIG, nombre=nombre, nit=nit,
            actividad=act, ingresos_brutos=Decimal(str(ingresos)),
        )
    print(f'{len(contribuyentes)} contribuyentes ICA ejemplo creados')


def crear_rubros_ingreso():
    RubroIngreso.objects.filter(vigencia=VIG).delete()

    # Helper to create rubros
    def r(codigo, desc, parent=None, metodo='MAN', recaudo=0, tarifa_poai=None,
          valor=0, fuente='', nom_fuente='', es_titulo=False, orden=0, nivel=0, obs=''):
        return RubroIngreso.objects.create(
            vigencia=VIG, codigo=codigo, descripcion=desc, parent=parent,
            metodo_calculo=metodo, recaudo_vigencia_anterior=Decimal(str(recaudo)),
            tarifa_poai=Decimal(str(tarifa_poai)) if tarifa_poai else None,
            valor_apropiacion=Decimal(str(valor)),
            codigo_fuente=fuente, nombre_fuente=nom_fuente,
            es_titulo=es_titulo, orden=orden, nivel=nivel, observaciones=obs,
        )

    # NIVEL 0 - Gran Total
    total = r('0', 'ADMINISTRACIÓN CENTRAL', es_titulo=True, orden=1, nivel=0)

    # NIVEL 1
    corrientes = r('1.1', 'INGRESOS CORRIENTES', parent=total, es_titulo=True, orden=10, nivel=1)
    capital = r('1.2', 'RECURSOS DE CAPITAL', parent=total, es_titulo=True, orden=200, nivel=1)
    fondos = r('1.3', 'FONDOS ESPECIALES', parent=total, es_titulo=True, orden=300, nivel=1)

    # NIVEL 2 - Tributarios
    tributarios = r('1.1.01', 'INGRESOS TRIBUTARIOS', parent=corrientes, es_titulo=True, orden=11, nivel=2)
    no_tributarios = r('1.1.02', 'INGRESOS NO TRIBUTARIOS', parent=corrientes, es_titulo=True, orden=100, nivel=2)

    # NIVEL 3 - Directos e Indirectos
    directos = r('1.1.01.01', 'IMPUESTOS DIRECTOS', parent=tributarios, es_titulo=True, orden=12, nivel=3)
    indirectos = r('1.1.01.02', 'IMPUESTOS INDIRECTOS', parent=tributarios, es_titulo=True, orden=30, nivel=3)

    # NIVEL 4 - Predial Unificado
    predial = r('1.1.01.01.200', 'PREDIAL UNIFICADO', parent=directos, es_titulo=True, orden=13, nivel=4,
                fuente='2', nom_fuente='PROPIOS')

    # NIVEL 5 - Detalle Predial
    r('1.1.01.01.200.01', 'Predial Urbano - Vigencia Actual', parent=predial,
      metodo='PUVA', orden=14, nivel=5, fuente='2', nom_fuente='PROPIOS',
      obs='Calculado desde base catastral urbana x tarifa x cultura de pago')
    r('1.1.01.01.200.02', 'Predial Urbano - Vigencias Anteriores', parent=predial,
      metodo='PUAN', orden=15, nivel=5, fuente='2', nom_fuente='PROPIOS',
      obs='Cartera x %base x %urbano')
    r('1.1.01.01.200.03', 'Predial Rural - Vigencia Actual', parent=predial,
      metodo='PRVA', orden=16, nivel=5, fuente='2', nom_fuente='PROPIOS',
      obs='Calculado desde base catastral rural x tarifa x cultura de pago')
    r('1.1.01.01.200.04', 'Predial Rural - Vigencias Anteriores', parent=predial,
      metodo='PRAN', orden=17, nivel=5, fuente='2', nom_fuente='PROPIOS',
      obs='Cartera x %base x %rural')

    # NIVEL 4 - ICA
    ica = r('1.1.01.02.200', 'INDUSTRIA Y COMERCIO', parent=indirectos, es_titulo=True, orden=31, nivel=4,
            fuente='2', nom_fuente='PROPIOS')

    r('1.1.01.02.200.01', 'ICA - Actividades Industriales', parent=ica,
      metodo='ICAI', orden=32, nivel=5, fuente='2', nom_fuente='PROPIOS',
      obs='Ingresos brutos x (1+PIB) x tarifa industrial')
    r('1.1.01.02.200.02', 'ICA - Actividades de Servicios', parent=ica,
      metodo='ICAS', orden=33, nivel=5, fuente='2', nom_fuente='PROPIOS',
      obs='Ingresos brutos x (1+PIB) x tarifa servicios')
    r('1.1.01.02.200.03', 'ICA - Actividades Comerciales', parent=ica,
      metodo='ICAC', orden=34, nivel=5, fuente='2', nom_fuente='PROPIOS',
      obs='Ingresos brutos x (1+PIB) x tarifa comercial')

    # Avisos y Tableros
    r('1.1.01.02.201', 'Avisos y Tableros', parent=indirectos,
      metodo='AT', orden=35, nivel=4, fuente='2', nom_fuente='PROPIOS',
      obs='15% del total de ICA')

    # Impuestos con IPC
    r('1.1.01.02.204', 'Impuesto de Publicidad Exterior Visual', parent=indirectos,
      metodo='IPC', recaudo=150000000, orden=36, nivel=4, fuente='2', nom_fuente='PROPIOS',
      obs='Aplica incremento IPC sobre recaudo anterior')
    r('1.1.01.02.208', 'Impuesto de Circulación y Tránsito', parent=indirectos,
      metodo='IPC', recaudo=80000000, orden=37, nivel=4, fuente='2', nom_fuente='PROPIOS',
      obs='Aplica incremento IPC')
    r('1.1.01.02.209', 'Impuesto de Delineación Urbana', parent=indirectos,
      metodo='IPC', recaudo=120000000, orden=38, nivel=4, fuente='2', nom_fuente='PROPIOS',
      obs='Aplica incremento IPC')
    r('1.1.01.02.214', 'Impuesto al Transporte por Oleoductos', parent=indirectos,
      metodo='MAN', valor=14107935272, orden=39, nivel=4, fuente='2', nom_fuente='PROPIOS',
      obs='Aplica promedio geométrico')
    r('1.1.01.02.215', 'Impuesto de Alumbrado Público', parent=indirectos,
      metodo='IPC', recaudo=4500000000, orden=40, nivel=4, fuente='2', nom_fuente='PROPIOS',
      obs='Aplica incremento IPC')

    # No Tributarios
    contrib = r('1.1.02.01', 'CONTRIBUCIONES', parent=no_tributarios, es_titulo=True, orden=101, nivel=3)
    r('1.1.02.01.001', 'Contribución Sector Eléctrico', parent=contrib,
      metodo='IPC', recaudo=200000000, orden=102, nivel=4, fuente='2', nom_fuente='PROPIOS',
      obs='Aplica incremento IPC')
    r('1.1.02.01.002', 'Contribución por Estratificación', parent=contrib,
      metodo='IPC', recaudo=50000000, orden=103, nivel=4, fuente='2', nom_fuente='PROPIOS')

    tasas = r('1.1.02.02', 'TASAS Y DERECHOS', parent=no_tributarios, es_titulo=True, orden=110, nivel=3)
    r('1.1.02.02.001', 'Tasa Pro-Deporte y Recreación', parent=tasas,
      metodo='POAI', tarifa_poai=0.025, orden=111, nivel=4, fuente='2', nom_fuente='PROPIOS',
      obs='2.5% sobre POAI inversión sin Educación, Vivienda, Salud')

    multas = r('1.1.02.03', 'MULTAS, SANCIONES E INTERESES', parent=no_tributarios, es_titulo=True, orden=120, nivel=3)
    r('1.1.02.03.001', 'Multas de Gobierno', parent=multas,
      metodo='IPC', recaudo=30000000, orden=121, nivel=4, fuente='2', nom_fuente='PROPIOS')
    r('1.1.02.03.002', 'Intereses Moratorios', parent=multas,
      metodo='IPC', recaudo=100000000, orden=122, nivel=4, fuente='2', nom_fuente='PROPIOS')

    rend = r('1.1.02.04', 'RENTAS CONTRACTUALES Y RENDIMIENTOS', parent=no_tributarios,
             es_titulo=True, orden=130, nivel=3)
    r('1.1.02.04.001', 'Rendimientos Financieros - Recursos Propios', parent=rend,
      metodo='IPC', recaudo=300000000, orden=131, nivel=4, fuente='2', nom_fuente='PROPIOS',
      obs='Aplica incremento IPC')

    # Recursos de Capital
    r('1.2.07', 'Crédito Interno', parent=capital,
      metodo='MAN', valor=28125000000, orden=201, nivel=2, fuente='2', nom_fuente='PROPIOS',
      obs='Según cupo de endeudamiento')

    # Fondos Especiales - SGP
    sgp = r('1.3.01', 'SISTEMA GENERAL DE PARTICIPACIONES', parent=fondos, es_titulo=True, orden=301, nivel=2)

    r('1.3.01.01', 'SGP - Educación', parent=sgp,
      metodo='ICN', recaudo=4000000000, orden=302, nivel=3, fuente='17', nom_fuente='SGP Educación',
      obs='Aplica tasa crecimiento ICN 8%')
    r('1.3.01.02', 'SGP - Salud', parent=sgp,
      metodo='ICN', recaudo=2500000000, orden=303, nivel=3, fuente='20', nom_fuente='SGP Salud',
      obs='Aplica tasa crecimiento ICN 8%')
    r('1.3.01.03', 'SGP - Régimen Subsidiado', parent=sgp,
      metodo='ICN', recaudo=13000000000, orden=304, nivel=3, fuente='22', nom_fuente='SGP Rég. Subsidiado',
      obs='Aplica tasa crecimiento ICN 8%')
    r('1.3.01.04', 'SGP - Agua Potable y Saneamiento', parent=sgp,
      metodo='ICN', recaudo=1800000000, orden=305, nivel=3, fuente='28', nom_fuente='SGP APSB',
      obs='Aplica tasa crecimiento ICN 8%')
    r('1.3.01.05', 'SGP - Libre Inversión', parent=sgp,
      metodo='ICN', recaudo=1500000000, orden=306, nivel=3, fuente='4', nom_fuente='SGP Libre Inversión',
      obs='Aplica tasa crecimiento ICN 8%')
    r('1.3.01.06', 'SGP - Deporte', parent=sgp,
      metodo='ICN', recaudo=350000000, orden=307, nivel=3, fuente='32', nom_fuente='SGP Deporte',
      obs='Aplica tasa crecimiento ICN 8%')
    r('1.3.01.07', 'SGP - Cultura', parent=sgp,
      metodo='ICN', recaudo=250000000, orden=308, nivel=3, fuente='50', nom_fuente='SGP Cultura',
      obs='Aplica tasa crecimiento ICN 8%')

    # Estampillas
    estampillas = r('1.3.02', 'ESTAMPILLAS', parent=fondos, es_titulo=True, orden=320, nivel=2)
    r('1.3.02.01', 'Estampilla Pro Adulto Mayor (80%)', parent=estampillas,
      metodo='POAI', tarifa_poai=0.04, orden=321, nivel=3, fuente='2', nom_fuente='PROPIOS',
      obs='4% del POAI inversión sin Educación, Vivienda, Salud')
    r('1.3.02.02', 'Estampilla Pro Electrificación Rural (80%)', parent=estampillas,
      metodo='POAI', tarifa_poai=0.01, orden=322, nivel=3, fuente='2', nom_fuente='PROPIOS',
      obs='1% del POAI inversión')
    r('1.3.02.03', 'Estampilla Pro Turismo (80%)', parent=estampillas,
      metodo='POAI', tarifa_poai=0.02, orden=323, nivel=3, fuente='2', nom_fuente='PROPIOS',
      obs='2% del POAI inversión')
    r('1.3.02.04', 'Estampilla Procultura (60%)', parent=estampillas,
      metodo='POAI', tarifa_poai=0.02, orden=324, nivel=3, fuente='2', nom_fuente='PROPIOS',
      obs='2% del POAI inversión')
    r('1.3.02.05', 'Estampilla Justicia Familiar', parent=estampillas,
      metodo='POAI', tarifa_poai=0.02, orden=325, nivel=3, fuente='2', nom_fuente='PROPIOS',
      obs='2% del POAI inversión')

    print(f'Rubros de ingreso creados: {RubroIngreso.objects.filter(vigencia=VIG).count()}')


if __name__ == '__main__':
    print('=' * 60)
    print('SIPRE - Creando datos iniciales para Puerto López')
    print('=' * 60)
    crear_usuario()
    crear_parametros()
    crear_tarifas_predial()
    crear_cultura_pago()
    crear_contribuyentes_predial_ejemplo()
    crear_carteras()
    crear_tarifas_ica()
    crear_contribuyentes_ica_ejemplo()
    crear_rubros_ingreso()
    print('=' * 60)
    print('¡Datos iniciales creados exitosamente!')
    print('Usuarios disponibles:')
    print('  admin / admin123  (superusuario)')
    print('  presupuesto / Puerto2026  (usuario normal)')
    print('=' * 60)
