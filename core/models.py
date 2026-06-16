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

    # ===== GASTOS: Personal y Prestaciones (Ley 100/1993, Ley 4/1992, CST) =====
    pct_incremento_salarial = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal('0.081'),
                                                    verbose_name='% Incremento Salarial Anual',
                                                    help_text='Decreto salarial anual del Gobierno. Ej: 0.081 = 8.1% (proy 2027)')
    subsidio_transporte_mensual = models.DecimalField(max_digits=12, decimal_places=2,
                                                        default=Decimal('274000'),
                                                        verbose_name='Subsidio Transporte Mensual ($)',
                                                        help_text='Aplica a empleados con sueldo ≤ 2 SMLMV. Decreto SMLMV anual.')
    # Aportes Seguridad Social (Ley 100/1993)
    pct_aporte_pension = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal('0.12'),
                                               verbose_name='% Aporte Pensión Empleador',
                                               help_text='Ley 100/1993 art. 22. Default 12%')
    pct_aporte_salud = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal('0.085'),
                                             verbose_name='% Aporte Salud Empleador',
                                             help_text='Ley 100/1993 art. 204. Default 8.5%')
    pct_aporte_arl = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal('0.00522'),
                                           verbose_name='% Aporte ARL',
                                           help_text='Decreto 1295/1994. Varía por clase de riesgo. Default 0.522% (clase I)')
    pct_cesantias = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal('0.0833'),
                                          verbose_name='% Cesantías',
                                          help_text='Ley 50/1990 art. 99. Default 8.33%')
    pct_intereses_cesantias = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal('0.12'),
                                                    verbose_name='% Intereses Cesantías',
                                                    help_text='Ley 52/1975. Default 12% anual sobre cesantías')
    # Prestaciones Sociales
    pct_prima_servicios = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal('0.0417'),
                                                verbose_name='% Prima de Servicios',
                                                help_text='Sector público: 15 días = 4.17% (Dto 1042/78 art. 58). Sector privado: 8.33% = 1 mes.')
    pct_prima_navidad = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal('0.0833'),
                                              verbose_name='% Prima de Navidad',
                                              help_text='Ley 41/1975. Default 8.33% = 1 mes/año')
    pct_prima_vacaciones = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal('0.0417'),
                                                 verbose_name='% Prima de Vacaciones',
                                                 help_text='Ley 4/1992. Default 4.17% = 15 días/año')
    pct_bonif_servicios_prestados = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal('0.50'),
                                                          verbose_name='% BSP Sueldo Bajo (≤ umbral)',
                                                          help_text='Decreto 1042/1978 art. 45 + Dto 330/2018. Default 50% para sueldos ≤ 2 SMLMV')
    pct_bonif_servicios_prestados_alto = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal('0.35'),
                                                               verbose_name='% BSP Sueldo Alto (> umbral)',
                                                               help_text='Decreto 1042/1978 art. 45 + Dto 330/2018. Default 35% para sueldos > 2 SMLMV')
    umbral_smlmv_bsp = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('2.00'),
                                             verbose_name='Umbral SMLMV para BSP',
                                             help_text='Si salario_mensual ≤ umbral × SMLMV → BSP bajo; sino BSP alto. Dto 1042/78.')
    pct_bonif_recreacion = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal('0.0139'),
                                                 verbose_name='% Bonificación Recreación',
                                                 help_text='Decreto 451/1984. Default ~2 días salario (1.39%)')
    # Aportes Parafiscales (Ley 21/1982)
    pct_aporte_sena = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal('0.02'),
                                            verbose_name='% Aporte SENA',
                                            help_text='Ley 21/1982 art. 7. Default 2%')
    pct_aporte_icbf = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal('0.03'),
                                            verbose_name='% Aporte ICBF',
                                            help_text='Ley 7/1979 art. 2. Default 3%')
    pct_aporte_caja = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal('0.04'),
                                            verbose_name='% Aporte Caja Compensación',
                                            help_text='Ley 21/1982 art. 7. Default 4%')
    pct_aporte_esap = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal('0.005'),
                                            verbose_name='% Aporte ESAP',
                                            help_text='Ley 21/1982 art. 7. Default 0.5%')
    pct_aporte_escuelas = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal('0.01'),
                                                verbose_name='% Aporte Escuelas Industriales',
                                                help_text='Ley 21/1982 art. 7. Default 1%')
    # Pensionados (Ley 100/1993 art. 14)
    pct_incremento_pensionados = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal('0.040'),
                                                       verbose_name='% Incremento Mesada Pensionados',
                                                       help_text='Ley 100/1993 art. 14: incremento igual al IPC del año anterior.')
    # Servicio Deuda (Ley 358/1997)
    tcr_deuda = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal('0.921'),
                                      verbose_name='Tasa Cobertura Riesgo (TCR)',
                                      help_text='Factor multiplicador de intereses para cubrir riesgo. Default 0.921')
    pct_limite_intereses_ley358 = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('40.00'),
                                                        verbose_name='% Límite Intereses/Ahorro Operacional (Ley 358)',
                                                        help_text='Ley 358/1997 art. 6. Max 40%')
    pct_limite_saldo_deuda_ley358 = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('80.00'),
                                                          verbose_name='% Límite Saldo Deuda/Ingresos Corrientes (Ley 358)',
                                                          help_text='Ley 358/1997 art. 6. Max 80%')
    # Ley 617/2000 - Limite Gastos Funcionamiento
    pct_limite_funcionamiento_ley617 = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('80.00'),
                                                             verbose_name='% Límite Gastos Funcionamiento (Ley 617)',
                                                             help_text='% máximo sobre ICLD. Categorías: Esp=50, 1=55, 2-3=60, 4-5=75, 6=80')

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

    def calcular_honorarios_concejo(self, valor_smlmv=None, vigencia=None):
        """Vr Honorarios = valor_sesion × (ord + extra) × num_concejales.

        Si valor_sesion_concejal está en 0 cae al cálculo legacy basado en SMLMV.
        Si no se pasa valor_smlmv pero sí vigencia, se consulta VariableMacro.
        """
        total_sesiones = self.sesiones_ordinarias + self.sesiones_extraordinarias
        if self.valor_sesion_concejal and self.valor_sesion_concejal > 0:
            return self.valor_sesion_concejal * total_sesiones * self.num_concejales
        if not valor_smlmv and vigencia:
            valor_smlmv = get_smlv(vigencia)
        return self.honorario_concejal_smlmv * (valor_smlmv or Decimal('0')) * total_sesiones * self.num_concejales

    def calcular_transferencia_concejo(self, icld_total, valor_smlmv, pct_icld_adicional):
        """Total Concejo = Vr Honorarios + ICLD × pct_icld_adicional.

        pct_icld_adicional es el % adicional del Excel (0.015 = 1.5%).
        """
        honorarios = self.calcular_honorarios_concejo(valor_smlmv)
        adicional = icld_total * (pct_icld_adicional or Decimal('0'))
        return honorarios + adicional

    def calcular_transferencia_personeria(self, vigencia, icld_total, valor_smlmv=None):
        """Transferencia personería según la lógica del Anexo 6.

        - Especial/1ª/2ª: ICLD × limite_personeria_pct_icld / 100
        - Cats con progresion SMLV (5ª, 6ª): SMLV de PersoneriaSMLVProgresion × SMLMV
        - 3ª/4ª: personeria_smlv_fijo × SMLMV

        Si valor_smlmv no se pasa o es 0/None, se consulta el SMLMV del año
        en VariableMacro automaticamente.
        """
        if self.categoria in (0, 1, 2):
            return icld_total * self.limite_personeria_pct_icld / Decimal('100')

        if not valor_smlmv:
            valor_smlmv = get_smlv(vigencia)

        smlv = None
        progresion = PersoneriaSMLVProgresion.objects.filter(
            vigencia=vigencia, categoria=self.categoria
        ).first()
        if progresion:
            smlv = progresion.smlv
        elif self.personeria_smlv_fijo:
            smlv = self.personeria_smlv_fijo

        if smlv and valor_smlmv:
            return Decimal(smlv) * Decimal(valor_smlmv)
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


class VariableMacro(models.Model):
    """Variables macroeconomicas por año (Excel 'Variables Macro').

    Permite que SMLMV, IPC, PIB, etc. se consulten por anio en lugar de
    almacenarse como un solo valor en ParametrosSistema. Asi, cambiar la
    vigencia activa toma automaticamente el valor proyectado/historico
    correspondiente al ano.
    """
    TIPO_CHOICES = [
        ('SMLV', 'Salario Mínimo Legal Vigente (SMLMV)'),
        ('IPC', 'Inflación (IPC)'),
        ('PIB', 'PIB Nacional ($ Corrientes)'),
        ('PETROLEO', 'Precio Barril Petróleo (US$)'),
        ('DTF', 'DTF (Tasa de interés)'),
        ('TRM', 'TRM (Tasa Cambio)'),
    ]
    anio = models.IntegerField(verbose_name='Año')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, verbose_name='Variable')
    valor = models.DecimalField(max_digits=20, decimal_places=4, default=0,
                                verbose_name='Valor')
    pct_anual = models.DecimalField(max_digits=8, decimal_places=4, default=0,
                                     verbose_name='% Crecimiento Anual',
                                     help_text='Ej: 0.062 = 6.2%')
    es_proyectado = models.BooleanField(default=False,
                                         verbose_name='¿Es proyección?',
                                         help_text='False = histórico real, True = proyección')

    class Meta:
        verbose_name = 'Variable Macro'
        verbose_name_plural = 'Variables Macro'
        unique_together = ['anio', 'tipo']
        ordering = ['tipo', 'anio']

    def __str__(self):
        return f'{self.get_tipo_display()} {self.anio}: {self.valor}'


def get_macro(anio, tipo):
    """Helper: obtiene el valor de una variable macro para un año."""
    obj = VariableMacro.objects.filter(anio=anio, tipo=tipo).first()
    return obj.valor if obj else None


def get_smlv(anio, fallback=None):
    return get_macro(anio, 'SMLV') or fallback or Decimal('0')


def get_ipc(anio, fallback=None):
    obj = VariableMacro.objects.filter(anio=anio, tipo='IPC').first()
    if obj:
        return obj.pct_anual if obj.pct_anual else obj.valor
    return fallback or Decimal('0')


def get_pib(anio, fallback=None):
    return get_macro(anio, 'PIB') or fallback or Decimal('0')


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
