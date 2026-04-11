from django.db import models
from decimal import Decimal


class ParametrosSistema(models.Model):
    vigencia = models.IntegerField(unique=True, verbose_name='Vigencia Fiscal')
    valor_uvt = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Valor UVT ($)')
    tasa_ipc = models.DecimalField(max_digits=6, decimal_places=4, verbose_name='Tasa IPC (%)',
                                   help_text='Ej: 0.051 para 5.1%')
    tasa_icn = models.DecimalField(max_digits=6, decimal_places=4, verbose_name='Tasa Crecimiento ICN (%)',
                                   help_text='Ej: 0.08 para 8%')
    tasa_pib_nominal = models.DecimalField(max_digits=6, decimal_places=4, verbose_name='Tasa PIB Nominal (%)',
                                           help_text='Ej: 0.062 para 6.2%')
    poai_total_inversion = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                               verbose_name='POAI Total Inversión (sin Educación, Vivienda, Salud)')
    # TCPA calculada de cifras históricas
    tcpa_ingresos = models.DecimalField(max_digits=8, decimal_places=4, default=0,
                                        verbose_name='TCPA Ingresos (%)',
                                        help_text='Tasa Compuesta Promedio Anual de ingresos últimos 4 años')
    tcpa_gastos = models.DecimalField(max_digits=8, decimal_places=4, default=0,
                                      verbose_name='TCPA Gastos (%)',
                                      help_text='Tasa Compuesta Promedio Anual de gastos últimos 4 años')
    # Parámetros de gastos
    categoria_municipio = models.IntegerField(default=6, verbose_name='Categoría del Municipio',
                                              help_text='1-6 o 0 para Especial')
    valor_smlmv = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                       verbose_name='Valor SMLMV ($)')
    pct_promedio_pagos = models.DecimalField(max_digits=6, decimal_places=2, default=0,
                                             verbose_name='% Promedio Pagos/Aprob. Definitiva',
                                             help_text='Para cálculo estampillas')
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Parámetro del Sistema'
        verbose_name_plural = 'Parámetros del Sistema'
        ordering = ['-vigencia']

    def __str__(self):
        return f'Parámetros Vigencia {self.vigencia}'

    def save(self, *args, **kwargs):
        if self.activo:
            ParametrosSistema.objects.filter(activo=True).exclude(pk=self.pk).update(activo=False)
        super().save(*args, **kwargs)


class CategoriaConcejoChoices(models.IntegerChoices):
    ESPECIAL = 0, 'Especial'
    PRIMERA = 1, 'Primera'
    SEGUNDA = 2, 'Segunda'
    TERCERA = 3, 'Tercera'
    CUARTA = 4, 'Cuarta'
    QUINTA = 5, 'Quinta'
    SEXTA = 6, 'Sexta'


class TablaConcejoPersoneria(models.Model):
    """Tabla de límites de Concejo y Personería según categoría del municipio (Ley 617/2000)"""
    categoria = models.IntegerField(choices=CategoriaConcejoChoices.choices, unique=True,
                                    verbose_name='Categoría Municipio')
    # Concejo
    honorario_concejal_smlmv = models.DecimalField(max_digits=6, decimal_places=2, default=0,
                                                     verbose_name='Honorario Concejal (factor SMLMV)')
    sesiones_ordinarias = models.IntegerField(default=70, verbose_name='Sesiones Ordinarias/Año')
    sesiones_extraordinarias = models.IntegerField(default=12, verbose_name='Sesiones Extraordinarias/Año')
    num_concejales = models.IntegerField(default=11, verbose_name='Número de Concejales')
    limite_concejo_pct_icld = models.DecimalField(max_digits=6, decimal_places=2, default=0,
                                                   verbose_name='Límite Concejo (% ICLD)')
    # Personería
    limite_personeria_pct_icld = models.DecimalField(max_digits=6, decimal_places=2, default=0,
                                                      verbose_name='Límite Personería (% ICLD)')

    class Meta:
        verbose_name = 'Tabla Concejo/Personería'
        verbose_name_plural = 'Tablas Concejo/Personería'
        ordering = ['categoria']

    def __str__(self):
        return f'Cat. {self.get_categoria_display()} - Concejo: {self.limite_concejo_pct_icld}% / Personería: {self.limite_personeria_pct_icld}%'

    def calcular_honorarios_concejo(self, valor_smlmv):
        """Calcula honorarios totales del concejo = honorario * sesiones * concejales"""
        total_sesiones = self.sesiones_ordinarias + self.sesiones_extraordinarias
        honorario_sesion = self.honorario_concejal_smlmv * valor_smlmv
        return honorario_sesion * total_sesiones * self.num_concejales

    def calcular_limite_concejo(self, icld_total):
        """Calcula el límite presupuestal del Concejo"""
        return icld_total * self.limite_concejo_pct_icld / Decimal('100')

    def calcular_limite_personeria(self, icld_total):
        """Calcula el límite presupuestal de la Personería"""
        return icld_total * self.limite_personeria_pct_icld / Decimal('100')


class VigenciaFutura(models.Model):
    """Vigencias futuras por fuentes de financiación"""
    ESTADO_CHOICES = [
        ('APR', 'Aprobada'),
        ('EJE', 'En Ejecución'),
    ]
    vigencia = models.IntegerField(verbose_name='Vigencia de Registro')
    vigencia_futura = models.IntegerField(verbose_name='Año de la Vigencia Futura')
    descripcion = models.CharField(max_length=500, verbose_name='Descripción / Objeto')
    codigo_fuente = models.CharField(max_length=20, verbose_name='Código Fuente')
    nombre_fuente = models.CharField(max_length=200, verbose_name='Nombre Fuente')
    valor = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name='Valor ($)')
    estado = models.CharField(max_length=3, choices=ESTADO_CHOICES, default='APR')
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Vigencia Futura'
        verbose_name_plural = 'Vigencias Futuras'
        ordering = ['vigencia_futura', 'codigo_fuente']

    def __str__(self):
        return f'VF {self.vigencia_futura} - {self.codigo_fuente}: ${self.valor:,.0f}'
