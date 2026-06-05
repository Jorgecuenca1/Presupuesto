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
    pct_pagos_despacho = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal('0.8000'),
                                             verbose_name='% Pagos Despacho y Secretarías',
                                             help_text='Peso del componente de despacho/secretarías sobre el % promedio pagos. Ej: 0.80 = 80%')
    pct_pagos_pensiones = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal('0.2000'),
                                              verbose_name='% Pagos Fondo de Pensiones',
                                              help_text='Peso del componente Fondo de Pensiones sobre el % promedio pagos. Ej: 0.20 = 20%')
    pct_crecimiento_viviendas = models.DecimalField(max_digits=8, decimal_places=6, default=Decimal('0.015'),
                                                     verbose_name='% Crecimiento Viviendas',
                                                     help_text='Incremento anual de viviendas para proyección predial urbano vivienda. Ej: 0.015 = 1.5%')
    pct_cartera_base = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('40.00'),
                                           verbose_name='% Base Recaudo Cartera',
                                           help_text='Porcentaje base de recaudo sobre el valor de cartera de vigencias anteriores. Ej: 40.00 = 40%')
    pct_cartera_urbano = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('10.00'),
                                             verbose_name='% Urbano Cartera',
                                             help_text='Porción de la cartera asignada a predial urbano. Ej: 10.00 = 10%')
    pct_cartera_rural = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('90.00'),
                                            verbose_name='% Rural Cartera',
                                            help_text='Porción de la cartera asignada a predial rural. Ej: 90.00 = 90%')
    pct_eficiencia_recaudo = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('70.00'),
                                                  verbose_name='% Eficiencia Recaudo',
                                                  help_text='Porcentaje global de eficiencia de recaudo (antes Cultura de Pago). Se aplica al recaudo potencial. Ej: 70.00 = 70%')

    # Cálculo de estampillas (Base Estampillas)
    gasto_sev_ppto_nc = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                            verbose_name='Gasto SEV Ppto NC ($)',
                                            help_text='Gasto apropiado en Salud, Educación y Vivienda sobre presupuesto NC')
    sgr_presupuesto = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                          verbose_name='Presupuesto SGR ($)')
    gasto_sev_sgr = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                        verbose_name='Gasto SEV SGR ($)',
                                        help_text='Gasto apropiado en Salud, Educación y Vivienda sobre SGR')
    pct_pagos_sin_sgr = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal('0.8483'),
                                            verbose_name='% Promedio Pagos sin SGR',
                                            help_text='Ej: 0.8483 = 84.83%. Promedio ppto últimas 3 vigencias sin SGR')
    pct_pagos_sgr = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal('0.3480'),
                                        verbose_name='% Promedio Pagos SGR',
                                        help_text='Ej: 0.3480 = 34.80%. Promedio ppto últimas 3 vigencias SGR')
    reservas_presupuestales_nc = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                                     verbose_name='Reservas Presupuestales NC ($)')
    cuentas_por_pagar_nc = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                               verbose_name='Cuentas por Pagar NC ($)')
    superavit_fiscal = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                           verbose_name='Superávit Fiscal Estimado ($)')

    # Datos históricos para el cálculo del Impuesto de Transporte por Oleoductos.
    # Se proyecta como promedio simple de los últimos 3 años de recaudo real.
    recaudo_oleoductos_anio_n3 = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                                      verbose_name='Recaudo Oleoductos hace 3 años ($)',
                                                      help_text='Recaudo histórico hace 3 años (vigencia - 3)')
    recaudo_oleoductos_anio_n2 = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                                      verbose_name='Recaudo Oleoductos hace 2 años ($)',
                                                      help_text='Recaudo histórico hace 2 años (vigencia - 2)')
    recaudo_oleoductos_anio_n1 = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                                      verbose_name='Recaudo Oleoductos año anterior ($)',
                                                      help_text='Recaudo histórico del año anterior (vigencia - 1)')

    # Anexo 6 Organos de Control
    icld_calculado = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                          verbose_name='ICLD vigencia anterior ($)',
                                          help_text='Ingresos Corrientes de Libre Destinación del año anterior. '
                                                    'Se autollena desde Cifras Históricas si está en 0; editable.')
    pct_icld_adicional_concejo = models.DecimalField(max_digits=6, decimal_places=4,
                                                       default=Decimal('0.015'),
                                                       verbose_name='% ICLD Adicional Concejo',
                                                       help_text='% sobre ICLD para sumar al Vr Honorarios del Concejo. '
                                                                 'Ej: 0.015 = 1.5% (Excel Anexo 6).')

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
    """Tabla de límites de Concejo y Personería según categoría del municipio.

    Estructura del Anexo 6 (Leyes 617/2000, 2461 y 2422):

    Concejo:
        Vr Honorarios   = valor_sesion × (ses_ord + ses_extra) × num_concejales
        % ICLD Adicional = ICLD × pct_icld_adicional_concejo / 100
        Total Concejo    = Vr Honorarios + % ICLD Adicional

    Personería (por categoría):
        Especial, 1ª, 2ª:  ICLD × limite_personeria_pct_icld / 100
        3ª, 4ª, 5ª, 6ª:    SMLV × valor_smlmv
                           El SMLV para 5ª sigue la progresión Ley 2461/2422
                           (210 en 2025, +10 por año hasta 250 en 2029). Para
                           categorías con SMLV fijo (3ª=400, 4ª=330, 6ª=0) se
                           guarda en personeria_smlv_fijo.
    """
    categoria = models.IntegerField(choices=CategoriaConcejoChoices.choices, unique=True,
                                    verbose_name='Categoría Municipio')
    # Concejo - parametros del Excel
    valor_sesion_concejal = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                                  verbose_name='Valor Sesión Concejal ($)',
                                                  help_text='Honorario por sesión (Ej. cat 5: $348.256)')
    sesiones_ordinarias = models.IntegerField(default=70, verbose_name='Sesiones Ordinarias/Año')
    sesiones_extraordinarias = models.IntegerField(default=12, verbose_name='Sesiones Extraordinarias/Año')
    num_concejales = models.IntegerField(default=11, verbose_name='Número de Concejales')
    # Legacy: factor SMLMV (no se usa con el Excel nuevo, se mantiene por compat)
    honorario_concejal_smlmv = models.DecimalField(max_digits=6, decimal_places=2, default=0,
                                                     verbose_name='Honorario Concejal (factor SMLMV)',
                                                     help_text='Legado. Solo si valor_sesion_concejal=0')
    limite_concejo_pct_icld = models.DecimalField(max_digits=6, decimal_places=2, default=0,
                                                   verbose_name='Límite Concejo (% ICLD)',
                                                   help_text='Tope legal Ley 617. Solo referencia.')
    # Personería
    limite_personeria_pct_icld = models.DecimalField(max_digits=6, decimal_places=2, default=0,
                                                      verbose_name='Límite Personería (% ICLD)',
                                                      help_text='Para Especial/1ª/2ª (cálculo por % ICLD)')
    personeria_smlv_fijo = models.IntegerField(default=0,
                                                verbose_name='Personería SMLV Fijo',
                                                help_text='Para categorías con SMLV fijo (3ª=400, 4ª=330, 6ª=0). '
                                                          'La 5ª usa la tabla PersoneriaSMLVProgresion por vigencia.')

    class Meta:
        verbose_name = 'Tabla Concejo/Personería'
        verbose_name_plural = 'Tablas Concejo/Personería'
        ordering = ['categoria']

    def __str__(self):
        return f'Cat. {self.get_categoria_display()}'

    def calcular_honorarios_concejo(self, valor_smlmv):
        """Vr Honorarios = valor_sesion × (ord + extra) × num_concejales.

        Si valor_sesion_concejal está en 0 cae al cálculo legacy
        (honorario_concejal_smlmv × valor_smlmv × sesiones × concejales).
        """
        total_sesiones = self.sesiones_ordinarias + self.sesiones_extraordinarias
        if self.valor_sesion_concejal and self.valor_sesion_concejal > 0:
            return self.valor_sesion_concejal * total_sesiones * self.num_concejales
        return self.honorario_concejal_smlmv * valor_smlmv * total_sesiones * self.num_concejales

    def calcular_transferencia_concejo(self, icld_total, valor_smlmv, pct_icld_adicional):
        """Total Concejo = Vr Honorarios + ICLD × pct_icld_adicional.

        pct_icld_adicional es el % adicional del Excel (0.015 = 1.5%).
        """
        honorarios = self.calcular_honorarios_concejo(valor_smlmv)
        adicional = icld_total * (pct_icld_adicional or Decimal('0'))
        return honorarios + adicional

    def calcular_transferencia_personeria(self, vigencia, icld_total, valor_smlmv):
        """Transferencia personería según la lógica del Anexo 6.

        - Especial/1ª/2ª: ICLD × limite_personeria_pct_icld / 100
        - 5ª (Puerto López): SMLV de PersoneriaSMLVProgresion(vigencia, categoria=5) × valor_smlmv
        - 3ª/4ª/6ª: personeria_smlv_fijo × valor_smlmv
        """
        if self.categoria in (0, 1, 2):
            return icld_total * self.limite_personeria_pct_icld / Decimal('100')

        smlv = None
        progresion = PersoneriaSMLVProgresion.objects.filter(
            vigencia=vigencia, categoria=self.categoria
        ).first()
        if progresion:
            smlv = progresion.smlv
        elif self.personeria_smlv_fijo:
            smlv = self.personeria_smlv_fijo

        if smlv:
            return Decimal(smlv) * valor_smlmv
        return Decimal('0')

    def calcular_limite_concejo(self, icld_total):
        """Tope legal Ley 617 sobre el Concejo (referencia, no es el monto a transferir)."""
        return icld_total * self.limite_concejo_pct_icld / Decimal('100')

    def calcular_limite_personeria(self, icld_total):
        """Tope legal Ley 617 sobre la Personería (referencia)."""
        return icld_total * self.limite_personeria_pct_icld / Decimal('100')


class PersoneriaSMLVProgresion(models.Model):
    """Progresión anual de SMLV para Personería por categoría municipal.

    La Ley 2461/2422 estableció una progresión para algunas categorías:
    p. ej. categoría 5: 2025=210, 2026=220, 2027=230, 2028=240, 2029=250.
    """
    vigencia = models.IntegerField(verbose_name='Vigencia Fiscal')
    categoria = models.IntegerField(choices=CategoriaConcejoChoices.choices,
                                    verbose_name='Categoría Municipio')
    smlv = models.IntegerField(verbose_name='SMLV',
                                help_text='Número de salarios mínimos legales vigentes (Ej: 220)')

    class Meta:
        verbose_name = 'Progresión SMLV Personería'
        verbose_name_plural = 'Progresiones SMLV Personería'
        unique_together = ['vigencia', 'categoria']
        ordering = ['categoria', 'vigencia']

    def __str__(self):
        return f'Cat. {self.get_categoria_display()} {self.vigencia}: {self.smlv} SMLV'


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
