from django.db import models


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
