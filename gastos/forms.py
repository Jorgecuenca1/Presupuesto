from django import forms
from .models import (
    RubroGasto, SeccionGasto, FuenteFinanciacion, EjecucionGasto,
    CifraHistoricaGasto, ServicioDeuda, CostoPersonal,
    ContratoCredito, PagareCredito, AmortizacionPagare,
)

W = 'form-control'


class SeccionGastoForm(forms.ModelForm):
    class Meta:
        model = SeccionGasto
        fields = '__all__'
        widgets = {
            'vigencia': forms.NumberInput(attrs={'class': W}),
            'codigo': forms.TextInput(attrs={'class': W}),
            'nombre': forms.TextInput(attrs={'class': W}),
        }


class FuenteFinanciacionForm(forms.ModelForm):
    class Meta:
        model = FuenteFinanciacion
        fields = '__all__'
        widgets = {
            'vigencia': forms.NumberInput(attrs={'class': W}),
            'codigo': forms.TextInput(attrs={'class': W}),
            'nombre': forms.TextInput(attrs={'class': W}),
        }


class RubroGastoForm(forms.ModelForm):
    class Meta:
        model = RubroGasto
        fields = ['vigencia', 'codigo', 'descripcion', 'seccion', 'fuente',
                  'codigo_fuente', 'nombre_fuente', 'tipo_gasto', 'metodo_calculo',
                  'parent', 'valor_apropiacion', 'observaciones', 'es_titulo',
                  'orden', 'nivel']
        widgets = {
            'vigencia': forms.NumberInput(attrs={'class': W}),
            'codigo': forms.TextInput(attrs={'class': W}),
            'descripcion': forms.TextInput(attrs={'class': W}),
            'seccion': forms.Select(attrs={'class': W}),
            'fuente': forms.Select(attrs={'class': W}),
            'codigo_fuente': forms.TextInput(attrs={'class': W}),
            'nombre_fuente': forms.TextInput(attrs={'class': W}),
            'tipo_gasto': forms.Select(attrs={'class': W}),
            'metodo_calculo': forms.Select(attrs={'class': W}),
            'parent': forms.Select(attrs={'class': W}),
            'valor_apropiacion': forms.NumberInput(attrs={'class': W}),
            'observaciones': forms.Textarea(attrs={'class': W, 'rows': 2}),
            'es_titulo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'orden': forms.NumberInput(attrs={'class': W}),
            'nivel': forms.NumberInput(attrs={'class': W}),
        }


class EjecucionGastoForm(forms.ModelForm):
    class Meta:
        model = EjecucionGasto
        fields = ['presupuesto_aprobado', 'adiciones', 'reducciones',
                  'traslado_credito', 'traslado_contra_credito',
                  'aplazamientos', 'desaplazamientos',
                  'cdp', 'compromisos', 'ordenado', 'pagado']
        widgets = {f: forms.NumberInput(attrs={'class': W, 'step': '0.01'})
                   for f in ['presupuesto_aprobado', 'adiciones', 'reducciones',
                             'traslado_credito', 'traslado_contra_credito',
                             'aplazamientos', 'desaplazamientos',
                             'cdp', 'compromisos', 'ordenado', 'pagado']}


class ImportarGastosExcelForm(forms.Form):
    archivo = forms.FileField(
        label='Archivo Excel (.xlsx)',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls'})
    )


class CifraHistoricaGastoForm(forms.ModelForm):
    class Meta:
        model = CifraHistoricaGasto
        fields = '__all__'
        widgets = {
            'vigencia_calculo': forms.NumberInput(attrs={'class': W}),
            'anio': forms.NumberInput(attrs={'class': W}),
            'codigo_rubro': forms.TextInput(attrs={'class': W}),
            'descripcion': forms.TextInput(attrs={'class': W}),
            'valor_apropiacion': forms.NumberInput(attrs={'class': W, 'step': '0.01'}),
            'valor_compromisos': forms.NumberInput(attrs={'class': W, 'step': '0.01'}),
            'valor_pagos': forms.NumberInput(attrs={'class': W, 'step': '0.01'}),
            'tipo_gasto': forms.Select(attrs={'class': W}),
        }


class ContratoCreditoForm(forms.ModelForm):
    class Meta:
        model = ContratoCredito
        fields = '__all__'
        widgets = {
            'vigencia': forms.NumberInput(attrs={'class': W}),
            'banco': forms.TextInput(attrs={'class': W}),
            'renta_pignorada': forms.TextInput(attrs={'class': W}),
            'objeto_credito': forms.Textarea(attrs={'class': W, 'rows': 2}),
            'valor_contrato': forms.NumberInput(attrs={'class': W, 'step': '0.01'}),
            'plazo_meses': forms.NumberInput(attrs={'class': W}),
            'codigo_fuente': forms.TextInput(attrs={'class': W}),
            'nombre_fuente': forms.TextInput(attrs={'class': W}),
            'observaciones': forms.Textarea(attrs={'class': W, 'rows': 2}),
        }


class PagareCreditoForm(forms.ModelForm):
    class Meta:
        model = PagareCredito
        fields = '__all__'
        widgets = {
            'contrato': forms.Select(attrs={'class': W}),
            'numero_pagare': forms.TextInput(attrs={'class': W}),
            'fecha_desembolso': forms.DateInput(attrs={'class': W, 'type': 'date'}),
            'valor_capital': forms.NumberInput(attrs={'class': W, 'step': '0.01'}),
            'tasa_ibr': forms.NumberInput(attrs={'class': W, 'step': '0.0001'}),
            'puntos': forms.NumberInput(attrs={'class': W, 'step': '0.0001'}),
            'tasa_cobertura_riesgo': forms.NumberInput(attrs={'class': W, 'step': '0.0001'}),
            'plazo_meses': forms.NumberInput(attrs={'class': W}),
            'observaciones': forms.Textarea(attrs={'class': W, 'rows': 2}),
        }


class AmortizacionPagareForm(forms.ModelForm):
    class Meta:
        model = AmortizacionPagare
        fields = ['vigencia_pago', 'capital_principal', 'intereses', 'intereses_tcr']
        widgets = {
            'vigencia_pago': forms.NumberInput(attrs={'class': W}),
            'capital_principal': forms.NumberInput(attrs={'class': W, 'step': '0.01'}),
            'intereses': forms.NumberInput(attrs={'class': W, 'step': '0.01'}),
            'intereses_tcr': forms.NumberInput(attrs={'class': W, 'step': '0.01'}),
        }


class CostoPersonalForm(forms.ModelForm):
    class Meta:
        model = CostoPersonal
        fields = '__all__'
        widgets = {f: forms.NumberInput(attrs={'class': W, 'step': '0.01'})
                   for f in ['vigencia', 'salario_basico', 'prima_navidad', 'prima_vacaciones',
                             'prima_servicios', 'cesantias', 'intereses_cesantias', 'vacaciones',
                             'aportes_salud', 'aportes_pension', 'aportes_arl', 'aportes_caja',
                             'aportes_icbf', 'aportes_sena', 'cantidad']}
        widgets['cargo'] = forms.TextInput(attrs={'class': W})
        widgets['grado'] = forms.TextInput(attrs={'class': W})
        widgets['seccion'] = forms.Select(attrs={'class': W})
        widgets['es_pensionado'] = forms.CheckboxInput(attrs={'class': 'form-check-input'})
        widgets['observaciones'] = forms.Textarea(attrs={'class': W, 'rows': 2})
