from django import forms
from .models import RubroGasto, SeccionGasto, FuenteFinanciacion, EjecucionGasto

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
                  'codigo_fuente', 'nombre_fuente', 'tipo_gasto', 'parent',
                  'valor_apropiacion', 'observaciones', 'es_titulo', 'orden', 'nivel']
        widgets = {
            'vigencia': forms.NumberInput(attrs={'class': W}),
            'codigo': forms.TextInput(attrs={'class': W}),
            'descripcion': forms.TextInput(attrs={'class': W}),
            'seccion': forms.Select(attrs={'class': W}),
            'fuente': forms.Select(attrs={'class': W}),
            'codigo_fuente': forms.TextInput(attrs={'class': W}),
            'nombre_fuente': forms.TextInput(attrs={'class': W}),
            'tipo_gasto': forms.Select(attrs={'class': W}),
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
