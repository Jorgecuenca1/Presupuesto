from django.db import models
from decimal import Decimal


class CategoriaPredial(models.TextChoices):
    URBANO_VIVIENDA = 'UV', 'Urbano - Vivienda'
    URBANO_EDIFICADO_FINANCIERO = 'UEF', 'Urbano Edificado - Act. Financieras'
    URBANO_EDIFICADO_DEMAS = 'UED', 'Urbano Edificado - Demás'
    URBANO_NO_EDIF_URBANIZABLE = 'UNEU', 'Urbano No Edificado - Urbanizable No Urbanizado'
    URBANO_NO_EDIF_URBANIZADO = 'UNUE', 'Urbano No Edificado - Urbanizado No Edificado'
    URBANO_NO_EDIF_NO_URBANIZABLE = 'UNNU', 'Urbano No Edificado - No Urbanizable'
    RURAL = 'RU', 'Rural'
    PARCELACION_EDIFICADO = 'PE', 'Parcelación/Finca Recreo - Edificado'
    PARCELACION_NO_EDIFICADO = 'PNE', 'Parcelación/Finca Recreo - No Edificado'


# Urbano edificados: vivienda, edificado demás, financieros.
# Los urbanos NO edificados (UNEU/UNUE/UNNU) se agrupan con RURAL en el reporte,
# aunque conservan su tarifa propia porque se filtran por su código de categoría.
CATEGORIAS_URBANAS = ['UV', 'UEF', 'UED']
CATEGORIAS_RURALES = ['RU', 'PE', 'PNE', 'UNEU', 'UNUE', 'UNNU']


class TarifaPredial(models.Model):
    vigencia = models.IntegerField()
    categoria = models.CharField(max_length=4, choices=CategoriaPredial.choices)
    uvt_desde = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                     help_text='Rango inferior en UVT (dejar vacío si tarifa fija)')
    uvt_hasta = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                     help_text='Rango superior en UVT (dejar vacío si sin límite)')
    tarifa_por_mil = models.DecimalField(max_digits=8, decimal_places=3, verbose_name='Tarifa (x/1000)')
    descripcion = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Tarifa Predial'
        verbose_name_plural = 'Tarifas Predial'
        ordering = ['vigencia', 'categoria', 'uvt_desde']

    def __str__(self):
        rango = ''
        if self.uvt_desde is not None:
            rango = f' [{self.uvt_desde}-{self.uvt_hasta or "∞"} UVT]'
        return f'{self.get_categoria_display()}{rango}: {self.tarifa_por_mil}‰'


class CulturaPago(models.Model):
    vigencia = models.IntegerField()
    categoria = models.CharField(max_length=4, choices=CategoriaPredial.choices)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='% Eficiencia Recaudo',
                                     help_text='Ej: 70.00 para 70%. Override por categoría; si no se define se usa el % global de Parámetros.')

    class Meta:
        verbose_name = 'Eficiencia Recaudo'
        verbose_name_plural = 'Eficiencia Recaudo'
        unique_together = ['vigencia', 'categoria']

    def __str__(self):
        return f'{self.get_categoria_display()}: {self.porcentaje}%'


class ContribuyentePredial(models.Model):
    vigencia = models.IntegerField()
    direccion = models.CharField(max_length=300, verbose_name='Dirección del Predio')
    nombre_predio = models.CharField(max_length=200, verbose_name='Nombre del Predio')
    propietario = models.CharField(max_length=300, verbose_name='Propietario')
    cedula_catastral = models.CharField(max_length=50, blank=True, verbose_name='Cédula Catastral')
    avaluo_catastral = models.DecimalField(max_digits=20, decimal_places=2, verbose_name='Avalúo Catastral ($)')
    categoria = models.CharField(max_length=4, choices=CategoriaPredial.choices, verbose_name='Categoría')
    tarifa_aplicada = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    impuesto_calculado = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = 'Contribuyente Predial'
        verbose_name_plural = 'Contribuyentes Predial'
        ordering = ['categoria', '-avaluo_catastral']

    def __str__(self):
        return f'{self.propietario} - {self.nombre_predio}'


class CarteraVigenciaAnterior(models.Model):
    vigencia_calculo = models.IntegerField(verbose_name='Vigencia de Cálculo')
    vigencia_cartera = models.IntegerField(verbose_name='Año de la Cartera')
    valor_cartera = models.DecimalField(max_digits=20, decimal_places=2, verbose_name='Valor Cartera ($)')
    porcentaje_base = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('40.00'),
                                          verbose_name='% Base Recaudo')
    porcentaje_urbano = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('10.00'),
                                            verbose_name='% Urbano')
    porcentaje_rural = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('90.00'),
                                           verbose_name='% Rural')

    class Meta:
        verbose_name = 'Cartera Vigencia Anterior'
        verbose_name_plural = 'Cartera Vigencias Anteriores'
        ordering = ['-vigencia_cartera']
        unique_together = ['vigencia_calculo', 'vigencia_cartera']

    def __str__(self):
        return f'Cartera {self.vigencia_cartera} - ${self.valor_cartera:,.0f}'

    @property
    def proyeccion_urbano(self):
        return self.valor_cartera * self.porcentaje_base / 100 * self.porcentaje_urbano / 100

    @property
    def proyeccion_rural(self):
        return self.valor_cartera * self.porcentaje_base / 100 * self.porcentaje_rural / 100


class ActividadICA(models.TextChoices):
    IND_101 = '101', 'Industrial - Actividad Industrial'
    COM_201 = '201', 'Comercial - Alimentos, Víveres, Insumos Agrícolas'
    COM_202 = '202', 'Comercial - Equipos Computación, Venta Móvil'
    COM_203 = '203', 'Comercial - Lubricantes, Combustibles, Licores'
    COM_204 = '204', 'Comercial - Otras Actividades Comerciales'
    SER_301 = '301', 'Servicios - Construcción, Transporte, Telecom'
    SER_302 = '302', 'Servicios - Otras Actividades de Servicios'
    FIN_401 = '401', 'Financiera'


TIPO_ACTIVIDAD_MAP = {
    '101': 'Industrial',
    '201': 'Comercial', '202': 'Comercial', '203': 'Comercial', '204': 'Comercial',
    '301': 'Servicios', '302': 'Servicios',
    '401': 'Financiera',
}


class TarifaICA(models.Model):
    vigencia = models.IntegerField()
    codigo_actividad = models.CharField(max_length=3, choices=ActividadICA.choices, verbose_name='Actividad')
    tarifa_por_mil = models.DecimalField(max_digits=8, decimal_places=3, verbose_name='Tarifa (x/1000)')
    descripcion = models.CharField(max_length=300, blank=True)

    class Meta:
        verbose_name = 'Tarifa ICA'
        verbose_name_plural = 'Tarifas ICA'
        unique_together = ['vigencia', 'codigo_actividad']

    def __str__(self):
        return f'{self.get_codigo_actividad_display()}: {self.tarifa_por_mil}‰'


class ContribuyenteICA(models.Model):
    vigencia = models.IntegerField()
    nombre = models.CharField(max_length=300, verbose_name='Nombre/Razón Social')
    nit = models.CharField(max_length=20, verbose_name='NIT')
    actividad = models.CharField(max_length=3, choices=ActividadICA.choices, verbose_name='Actividad Económica')
    ingresos_brutos = models.DecimalField(max_digits=20, decimal_places=2, verbose_name='Ingresos Brutos Declarados ($)')
    tarifa_aplicada = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    impuesto_calculado = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    ingresos_proyectados = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = 'Contribuyente ICA'
        verbose_name_plural = 'Contribuyentes ICA'
        ordering = ['actividad', '-ingresos_brutos']

    def __str__(self):
        return f'{self.nombre} ({self.nit})'

    @property
    def tipo_actividad(self):
        return TIPO_ACTIVIDAD_MAP.get(self.actividad, 'Otro')


class MetodoCalculo(models.TextChoices):
    PREDIAL_URBANO_VA = 'PUVA', 'Cálculo Predial Urbano Vig. Actual'
    PREDIAL_URBANO_VANT = 'PUAN', 'Cálculo Predial Urbano Vig. Anteriores'
    PREDIAL_RURAL_VA = 'PRVA', 'Cálculo Predial Rural Vig. Actual'
    PREDIAL_RURAL_VANT = 'PRAN', 'Cálculo Predial Rural Vig. Anteriores'
    ICA_INDUSTRIAL = 'ICAI', 'Cálculo ICA Industrial'
    ICA_COMERCIAL = 'ICAC', 'Cálculo ICA Comercial'
    ICA_SERVICIOS = 'ICAS', 'Cálculo ICA Servicios'
    AVISOS_TABLEROS = 'AT', '15% del Total ICA'
    IPC = 'IPC', 'Incremento IPC sobre Recaudo Anterior'
    ICN = 'ICN', 'Tasa Crecimiento ICN sobre Recaudo Anterior'
    POAI = 'POAI', 'Tarifa % sobre POAI Inversión'
    ESTAMPILLA = 'EST', 'Cálculo Estampilla (Base × Tarifa)'
    MANUAL = 'MAN', 'Valor Manual'


class Estampilla(models.Model):
    vigencia = models.IntegerField()
    nombre = models.CharField(max_length=120, verbose_name='Nombre Estampilla',
                               help_text='Ej: Adulto Mayor, Pro-cultura, Justicia Familiar')
    codigo_rubro = models.CharField(max_length=50, blank=True,
                                     verbose_name='Código Rubro Presupuestal',
                                     help_text='Opcional. Código al que se asocia la proyección')
    tarifa = models.DecimalField(max_digits=6, decimal_places=4,
                                  verbose_name='Tarifa',
                                  help_text='Ej: 0.02 = 2%. Se multiplica por la base de cálculo')
    descripcion = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Estampilla'
        verbose_name_plural = 'Estampillas'
        unique_together = ['vigencia', 'nombre']
        ordering = ['vigencia', 'nombre']

    def __str__(self):
        return f'{self.nombre} ({self.tarifa * 100:.2f}%)'


class RubroIngreso(models.Model):
    vigencia = models.IntegerField()
    codigo = models.CharField(max_length=50, verbose_name='Código Presupuestal')
    descripcion = models.CharField(max_length=400, verbose_name='Descripción')
    codigo_fuente = models.CharField(max_length=10, blank=True, verbose_name='Cód. Fuente')
    nombre_fuente = models.CharField(max_length=100, blank=True, verbose_name='Fuente')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='hijos')
    metodo_calculo = models.CharField(max_length=4, choices=MetodoCalculo.choices, default='MAN')
    estampilla = models.ForeignKey(Estampilla, null=True, blank=True, on_delete=models.SET_NULL,
                                    verbose_name='Estampilla asociada',
                                    help_text='Requerido cuando el método es Cálculo Estampilla')
    recaudo_vigencia_anterior = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                                     verbose_name='Recaudo Vig. Anterior ($)')
    tarifa_poai = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True,
                                       verbose_name='Tarifa POAI (%)', help_text='Ej: 0.025 para 2.5%')
    valor_apropiacion = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                            verbose_name='Valor Apropiación ($)')
    observaciones = models.TextField(blank=True)
    es_titulo = models.BooleanField(default=False, verbose_name='Es título/subtotal')
    orden = models.IntegerField(default=0)
    nivel = models.IntegerField(default=0, help_text='Nivel de jerarquía para indentación')

    class Meta:
        verbose_name = 'Rubro de Ingreso'
        verbose_name_plural = 'Rubros de Ingreso'
        ordering = ['orden']

    def __str__(self):
        return f'{self.codigo} - {self.descripcion}'

    def calcular_hijos(self):
        total = Decimal('0')
        for hijo in self.hijos.all():
            if hijo.es_titulo:
                total += hijo.calcular_hijos()
            else:
                total += hijo.valor_apropiacion
        self.valor_apropiacion = total
        self.save(update_fields=['valor_apropiacion'])
        return total


class CifraHistoricaIngreso(models.Model):
    """Cifras históricas de ingresos CUIPO 2022-2025 para cálculo de TCPA"""
    vigencia_calculo = models.IntegerField(verbose_name='Vigencia de Cálculo',
                                           help_text='Año para el cual se proyecta')
    anio = models.IntegerField(verbose_name='Año Histórico')
    codigo_rubro = models.CharField(max_length=50, verbose_name='Código Rubro')
    descripcion = models.CharField(max_length=400, verbose_name='Descripción')
    valor_recaudo = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                        verbose_name='Valor Recaudo ($)')
    es_icld = models.BooleanField(default=False, verbose_name='¿Es ICLD?',
                                   help_text='Ingreso Corriente de Libre Destinación')
    es_sgp = models.BooleanField(default=False, verbose_name='¿Es SGP?')
    es_sgp_libre = models.BooleanField(default=False, verbose_name='¿Es SGP Libre Asignación?')

    class Meta:
        verbose_name = 'Cifra Histórica Ingreso'
        verbose_name_plural = 'Cifras Históricas Ingresos'
        ordering = ['anio', 'codigo_rubro']
        unique_together = ['vigencia_calculo', 'anio', 'codigo_rubro']

    def __str__(self):
        return f'{self.anio} - {self.codigo_rubro}: ${self.valor_recaudo:,.0f}'


class ResumenCalculo(models.Model):
    vigencia = models.IntegerField()
    tipo = models.CharField(max_length=30, verbose_name='Tipo de Cálculo')
    categoria = models.CharField(max_length=100)
    descripcion_rango = models.CharField(max_length=200, blank=True)
    total_avaluo = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    tarifa_por_mil = models.DecimalField(max_digits=8, decimal_places=3, default=0)
    recaudo_potencial = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    cultura_pago = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    proyeccion = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    cantidad_predios = models.IntegerField(default=0)
    fecha_calculo = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Resumen de Cálculo'
        verbose_name_plural = 'Resúmenes de Cálculo'
        ordering = ['tipo', 'categoria']

    def __str__(self):
        return f'{self.tipo} - {self.categoria}: ${self.proyeccion:,.0f}'
