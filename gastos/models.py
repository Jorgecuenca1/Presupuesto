from django.db import models
from decimal import Decimal


class TipoGasto(models.TextChoices):
    FUNCIONAMIENTO = 'FUN', 'Funcionamiento'
    INVERSION = 'INV', 'Inversión'
    DEUDA = 'DEU', 'Servicio de la Deuda'


class SeccionGasto(models.Model):
    vigencia = models.IntegerField()
    codigo = models.CharField(max_length=10, verbose_name='Código Sección')
    nombre = models.CharField(max_length=200, verbose_name='Nombre Sección')

    class Meta:
        verbose_name = 'Sección Presupuestal'
        verbose_name_plural = 'Secciones Presupuestales'
        ordering = ['codigo']
        unique_together = ['vigencia', 'codigo']

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'


class FuenteFinanciacion(models.Model):
    vigencia = models.IntegerField()
    codigo = models.CharField(max_length=20, verbose_name='Código Fuente')
    nombre = models.CharField(max_length=200, verbose_name='Nombre Fuente')

    class Meta:
        verbose_name = 'Fuente de Financiación'
        verbose_name_plural = 'Fuentes de Financiación'
        ordering = ['codigo']
        unique_together = ['vigencia', 'codigo']

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'


class RubroGasto(models.Model):
    vigencia = models.IntegerField()
    codigo = models.CharField(max_length=80, verbose_name='Identificación Presupuestal')
    descripcion = models.CharField(max_length=500, verbose_name='Descripción')
    seccion = models.ForeignKey(SeccionGasto, null=True, blank=True, on_delete=models.SET_NULL,
                                verbose_name='Sección')
    fuente = models.ForeignKey(FuenteFinanciacion, null=True, blank=True, on_delete=models.SET_NULL,
                               verbose_name='Fuente')
    codigo_fuente = models.CharField(max_length=20, blank=True, verbose_name='Cód. Fuente')
    nombre_fuente = models.CharField(max_length=200, blank=True, verbose_name='Nombre Fuente')
    tipo_gasto = models.CharField(max_length=3, choices=TipoGasto.choices, default='FUN',
                                  verbose_name='Tipo de Gasto')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE,
                               related_name='hijos')
    valor_apropiacion = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                            verbose_name='Apropiación ($)')
    observaciones = models.TextField(blank=True)
    es_titulo = models.BooleanField(default=False, verbose_name='Es título/subtotal')
    orden = models.IntegerField(default=0)
    nivel = models.IntegerField(default=0, help_text='Nivel de jerarquía para indentación')

    class Meta:
        verbose_name = 'Rubro de Gasto'
        verbose_name_plural = 'Rubros de Gasto'
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


class EjecucionGasto(models.Model):
    rubro = models.OneToOneField(RubroGasto, on_delete=models.CASCADE, related_name='ejecucion')
    presupuesto_aprobado = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                                verbose_name='Presupuesto Aprobado')
    adiciones = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                    verbose_name='Adiciones')
    reducciones = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                      verbose_name='Reducciones')
    traslado_credito = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                           verbose_name='Traslado Crédito')
    traslado_contra_credito = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                                   verbose_name='Traslado Contra Crédito')
    aplazamientos = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                        verbose_name='Aplazamientos')
    desaplazamientos = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                           verbose_name='Desaplazamientos')
    cdp = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                              verbose_name='CDP')
    compromisos = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                      verbose_name='Compromisos')
    ordenado = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                   verbose_name='Obligaciones (Ordenado)')
    pagado = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                 verbose_name='Pagado')

    class Meta:
        verbose_name = 'Ejecución de Gasto'
        verbose_name_plural = 'Ejecución de Gastos'

    def __str__(self):
        return f'Ejecución: {self.rubro.codigo}'

    @property
    def apropiacion_definitiva(self):
        return (self.presupuesto_aprobado + self.adiciones - self.reducciones
                + self.traslado_credito - self.traslado_contra_credito
                - self.aplazamientos + self.desaplazamientos)

    @property
    def saldo_apropiacion(self):
        return self.apropiacion_definitiva - self.compromisos

    @property
    def saldo_por_ordenar(self):
        return self.compromisos - self.ordenado

    @property
    def saldo_por_pagar(self):
        return self.ordenado - self.pagado

    @property
    def porcentaje_ejecucion(self):
        if self.apropiacion_definitiva > 0:
            return (self.compromisos / self.apropiacion_definitiva * 100).quantize(Decimal('0.01'))
        return Decimal('0')
