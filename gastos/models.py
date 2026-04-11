from django.db import models
from decimal import Decimal


class TipoGasto(models.TextChoices):
    FUNCIONAMIENTO = 'FUN', 'Funcionamiento'
    INVERSION = 'INV', 'Inversión'
    DEUDA = 'DEU', 'Servicio de la Deuda'


class CifraHistoricaGasto(models.Model):
    """Cifras históricas de gastos CUIPO 2022-2025 para cálculo de TCPA"""
    vigencia_calculo = models.IntegerField(verbose_name='Vigencia de Cálculo')
    anio = models.IntegerField(verbose_name='Año Histórico')
    codigo_rubro = models.CharField(max_length=80, verbose_name='Código Rubro')
    descripcion = models.CharField(max_length=500, verbose_name='Descripción')
    valor_apropiacion = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                            verbose_name='Apropiación Definitiva ($)')
    valor_compromisos = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                            verbose_name='Compromisos ($)')
    valor_pagos = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                      verbose_name='Pagos ($)')
    tipo_gasto = models.CharField(max_length=3, choices=TipoGasto.choices, default='FUN')

    class Meta:
        verbose_name = 'Cifra Histórica Gasto'
        verbose_name_plural = 'Cifras Históricas Gastos'
        ordering = ['anio', 'codigo_rubro']
        unique_together = ['vigencia_calculo', 'anio', 'codigo_rubro']

    def __str__(self):
        return f'{self.anio} - {self.codigo_rubro}: ${self.valor_apropiacion:,.0f}'

    @property
    def pct_pagos_apropiacion(self):
        if self.valor_apropiacion > 0:
            return (self.valor_pagos / self.valor_apropiacion * 100).quantize(Decimal('0.01'))
        return Decimal('0')


class ContratoCredito(models.Model):
    """Contrato de empréstito con una entidad financiera"""
    vigencia = models.IntegerField(verbose_name='Vigencia de Registro')
    banco = models.CharField(max_length=200, verbose_name='Entidad Financiera / Banco')
    renta_pignorada = models.CharField(max_length=200, verbose_name='Renta Pignorada',
                                       help_text='Ej: ITO (Impuesto Transporte Oleoductos)')
    objeto_credito = models.CharField(max_length=500, verbose_name='Objeto del Crédito')
    valor_contrato = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                         verbose_name='Valor Total del Contrato ($)')
    plazo_meses = models.IntegerField(default=0, verbose_name='Plazo Total (meses)')
    codigo_fuente = models.CharField(max_length=20, blank=True, verbose_name='Código Fuente')
    nombre_fuente = models.CharField(max_length=200, blank=True, verbose_name='Fuente Financiación')
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Contrato de Crédito'
        verbose_name_plural = 'Contratos de Crédito'
        ordering = ['banco']

    def __str__(self):
        return f'{self.banco} - {self.renta_pignorada} - ${self.valor_contrato:,.0f}'

    @property
    def num_pagares(self):
        return self.pagares.count()

    @property
    def total_desembolsado(self):
        return self.pagares.aggregate(t=models.Sum('valor_capital'))['t'] or Decimal('0')


class PagareCredito(models.Model):
    """Pagaré / Desembolso de un contrato de crédito"""
    contrato = models.ForeignKey(ContratoCredito, on_delete=models.CASCADE, related_name='pagares')
    numero_pagare = models.CharField(max_length=50, verbose_name='Número de Pagaré')
    fecha_desembolso = models.DateField(null=True, blank=True, verbose_name='Fecha de Desembolso')
    valor_capital = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                        verbose_name='Valor Capital del Pagaré ($)')
    tasa_ibr = models.DecimalField(max_digits=8, decimal_places=4, default=0,
                                   verbose_name='Tasa IBR (%)',
                                   help_text='IBR de la semana de firma del pagaré')
    puntos = models.DecimalField(max_digits=8, decimal_places=4, default=0,
                                 verbose_name='Puntos Adicionales (%)',
                                 help_text='Determinados en el contrato con el banco')
    tasa_cobertura_riesgo = models.DecimalField(max_digits=8, decimal_places=4, default=0,
                                                verbose_name='Tasa Cobertura Riesgo - TCR (%)',
                                                help_text='Cambia trimestralmente según Superfinanciera')
    plazo_meses = models.IntegerField(default=0, verbose_name='Plazo del Pagaré (meses)')
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Pagaré de Crédito'
        verbose_name_plural = 'Pagarés de Crédito'
        ordering = ['contrato', 'numero_pagare']

    def __str__(self):
        return f'Pagaré {self.numero_pagare} - ${self.valor_capital:,.0f}'

    @property
    def tasa_interes_total(self):
        """IBR + Puntos"""
        return self.tasa_ibr + self.puntos

    @property
    def tasa_total_con_tcr(self):
        """IBR + Puntos + TCR"""
        return self.tasa_ibr + self.puntos + self.tasa_cobertura_riesgo


class AmortizacionPagare(models.Model):
    """Tabla de amortización por vigencia para cada pagaré"""
    pagare = models.ForeignKey(PagareCredito, on_delete=models.CASCADE, related_name='amortizaciones')
    vigencia_pago = models.IntegerField(verbose_name='Vigencia de Pago')
    capital_principal = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                            verbose_name='Capital (Principal) ($)')
    intereses = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                    verbose_name='Intereses sin TCR ($)')
    intereses_tcr = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                        verbose_name='Intereses TCR ($)')

    class Meta:
        verbose_name = 'Amortización de Pagaré'
        verbose_name_plural = 'Amortizaciones de Pagaré'
        ordering = ['vigencia_pago']
        unique_together = ['pagare', 'vigencia_pago']

    def __str__(self):
        return f'{self.pagare.numero_pagare} - {self.vigencia_pago}: ${self.total:,.0f}'

    @property
    def total(self):
        return self.capital_principal + self.intereses + self.intereses_tcr


# Keep old model for backwards compatibility during migration
class ServicioDeuda(models.Model):
    """Modelo legacy - usar ContratoCredito/PagareCredito en su lugar"""
    vigencia = models.IntegerField(verbose_name='Vigencia')
    entidad_financiera = models.CharField(max_length=200, verbose_name='Entidad Financiera')
    objeto_credito = models.CharField(max_length=500, verbose_name='Objeto del Crédito')
    valor_inicial = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    saldo_capital = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    tasa_interes = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    plazo_meses = models.IntegerField(default=0)
    meses_restantes = models.IntegerField(default=0)
    cuota_capital_anual = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    intereses_anual = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    codigo_fuente = models.CharField(max_length=20, blank=True)
    nombre_fuente = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Servicio de Deuda (Legacy)'
        verbose_name_plural = 'Servicios de Deuda (Legacy)'

    @property
    def total_servicio_anual(self):
        return self.cuota_capital_anual + self.intereses_anual


class CostoPersonal(models.Model):
    """Costo de personal por sección/dependencia"""
    vigencia = models.IntegerField(verbose_name='Vigencia')
    seccion = models.ForeignKey('SeccionGasto', null=True, blank=True, on_delete=models.SET_NULL,
                                verbose_name='Sección')
    cargo = models.CharField(max_length=200, verbose_name='Cargo')
    grado = models.CharField(max_length=20, blank=True, verbose_name='Grado')
    cantidad = models.IntegerField(default=1, verbose_name='Cantidad')
    salario_basico = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                         verbose_name='Salario Básico Mensual ($)')
    prima_navidad = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                        verbose_name='Prima de Navidad ($)')
    prima_vacaciones = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                           verbose_name='Prima de Vacaciones ($)')
    prima_servicios = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                          verbose_name='Prima de Servicios ($)')
    cesantias = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                    verbose_name='Cesantías ($)')
    intereses_cesantias = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                              verbose_name='Intereses Cesantías ($)')
    vacaciones = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                     verbose_name='Vacaciones ($)')
    aportes_salud = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                        verbose_name='Aportes Salud ($)')
    aportes_pension = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                          verbose_name='Aportes Pensión ($)')
    aportes_arl = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                      verbose_name='Aportes ARL ($)')
    aportes_caja = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                       verbose_name='Aportes Caja ($)')
    aportes_icbf = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                       verbose_name='Aportes ICBF ($)')
    aportes_sena = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                       verbose_name='Aportes SENA ($)')
    es_pensionado = models.BooleanField(default=False, verbose_name='¿Es pensionado?')
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Costo de Personal'
        verbose_name_plural = 'Costos de Personal'
        ordering = ['seccion', 'cargo']

    def __str__(self):
        return f'{self.cargo} x{self.cantidad} - ${self.costo_total_anual:,.0f}'

    @property
    def costo_salarial_anual(self):
        return self.salario_basico * 12 * self.cantidad

    @property
    def costo_prestaciones(self):
        return (self.prima_navidad + self.prima_vacaciones + self.prima_servicios +
                self.cesantias + self.intereses_cesantias + self.vacaciones) * self.cantidad

    @property
    def costo_aportes(self):
        return (self.aportes_salud + self.aportes_pension + self.aportes_arl +
                self.aportes_caja + self.aportes_icbf + self.aportes_sena) * self.cantidad

    @property
    def costo_total_anual(self):
        return self.costo_salarial_anual + self.costo_prestaciones + self.costo_aportes


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
