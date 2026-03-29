from django import forms
from .models import (
    TarifaPredial, CulturaPago, ContribuyentePredial,
    CarteraVigenciaAnterior, TarifaICA, ContribuyenteICA, RubroIngreso,
)

W = 'form-control'


class TarifaPredialForm(forms.ModelForm):
    class Meta:
        model = TarifaPredial
        fields = '__all__'
        widgets = {f: forms.NumberInput(attrs={'class': W}) if f != 'categoria' else forms.Select(attrs={'class': W})
                   for f in ['vigencia', 'categoria', 'uvt_desde', 'uvt_hasta', 'tarifa_por_mil']}
        widgets['descripcion'] = forms.TextInput(attrs={'class': W})
        widgets['vigencia'] = forms.NumberInput(attrs={'class': W})


class CulturaPagoForm(forms.ModelForm):
    class Meta:
        model = CulturaPago
        fields = '__all__'
        widgets = {
            'vigencia': forms.NumberInput(attrs={'class': W}),
            'categoria': forms.Select(attrs={'class': W}),
            'porcentaje': forms.NumberInput(attrs={'class': W, 'step': '0.01'}),
        }


class ContribuyentePredialForm(forms.ModelForm):
    class Meta:
        model = ContribuyentePredial
        fields = ['vigencia', 'direccion', 'nombre_predio', 'propietario', 'cedula_catastral',
                  'avaluo_catastral', 'categoria']
        widgets = {
            'vigencia': forms.NumberInput(attrs={'class': W}),
            'direccion': forms.TextInput(attrs={'class': W}),
            'nombre_predio': forms.TextInput(attrs={'class': W}),
            'propietario': forms.TextInput(attrs={'class': W}),
            'cedula_catastral': forms.TextInput(attrs={'class': W}),
            'avaluo_catastral': forms.NumberInput(attrs={'class': W}),
            'categoria': forms.Select(attrs={'class': W}),
        }


class ImportarExcelForm(forms.Form):
    archivo = forms.FileField(
        label='Archivo Excel (.xlsx)',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls,.csv'})
    )


class CarteraForm(forms.ModelForm):
    class Meta:
        model = CarteraVigenciaAnterior
        fields = '__all__'
        widgets = {f: forms.NumberInput(attrs={'class': W, 'step': '0.01'}) for f in
                   ['vigencia_calculo', 'vigencia_cartera', 'valor_cartera',
                    'porcentaje_base', 'porcentaje_urbano', 'porcentaje_rural']}


class TarifaICAForm(forms.ModelForm):
    class Meta:
        model = TarifaICA
        fields = '__all__'
        widgets = {
            'vigencia': forms.NumberInput(attrs={'class': W}),
            'codigo_actividad': forms.Select(attrs={'class': W}),
            'tarifa_por_mil': forms.NumberInput(attrs={'class': W, 'step': '0.001'}),
            'descripcion': forms.TextInput(attrs={'class': W}),
        }


class ContribuyenteICAForm(forms.ModelForm):
    class Meta:
        model = ContribuyenteICA
        fields = ['vigencia', 'nombre', 'nit', 'actividad', 'ingresos_brutos']
        widgets = {
            'vigencia': forms.NumberInput(attrs={'class': W}),
            'nombre': forms.TextInput(attrs={'class': W}),
            'nit': forms.TextInput(attrs={'class': W}),
            'actividad': forms.Select(attrs={'class': W}),
            'ingresos_brutos': forms.NumberInput(attrs={'class': W}),
        }


class RubroIngresoForm(forms.ModelForm):
    class Meta:
        model = RubroIngreso
        fields = ['vigencia', 'codigo', 'descripcion', 'codigo_fuente', 'nombre_fuente',
                  'parent', 'metodo_calculo', 'recaudo_vigencia_anterior', 'tarifa_poai',
                  'valor_apropiacion', 'observaciones', 'es_titulo', 'orden', 'nivel']
        widgets = {
            'vigencia': forms.NumberInput(attrs={'class': W}),
            'codigo': forms.TextInput(attrs={'class': W}),
            'descripcion': forms.TextInput(attrs={'class': W}),
            'codigo_fuente': forms.TextInput(attrs={'class': W}),
            'nombre_fuente': forms.TextInput(attrs={'class': W}),
            'parent': forms.Select(attrs={'class': W}),
            'metodo_calculo': forms.Select(attrs={'class': W}),
            'recaudo_vigencia_anterior': forms.NumberInput(attrs={'class': W}),
            'tarifa_poai': forms.NumberInput(attrs={'class': W, 'step': '0.0001'}),
            'valor_apropiacion': forms.NumberInput(attrs={'class': W}),
            'observaciones': forms.Textarea(attrs={'class': W, 'rows': 2}),
            'es_titulo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'orden': forms.NumberInput(attrs={'class': W}),
            'nivel': forms.NumberInput(attrs={'class': W}),
        }
