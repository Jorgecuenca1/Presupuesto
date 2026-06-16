from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import ParametrosSistema, TablaConcejoPersoneria, VigenciaFutura


class LoginForm(forms.Form):
    username = forms.CharField(label='Usuario', max_length=150,
                               widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Usuario'}))
    password = forms.CharField(label='Contraseña',
                               widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}))


class RegistroForm(UserCreationForm):
    first_name = forms.CharField(label='Nombres', max_length=30,
                                 widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label='Apellidos', max_length=30,
                                widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Email',
                             widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.setdefault('class', 'form-control')


class ParametrosForm(forms.ModelForm):
    class Meta:
        model = ParametrosSistema
        fields = '__all__'
        widgets = {
            'vigencia': forms.NumberInput(attrs={'class': 'form-control'}),
            'valor_uvt': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tasa_ipc': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'tasa_icn': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'tasa_pib_nominal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'poai_total_inversion': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tcpa_ingresos': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001', 'readonly': True}),
            'tcpa_gastos': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001', 'readonly': True}),
            'categoria_municipio': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 6}),
            'valor_smlmv': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pct_promedio_pagos': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pct_pagos_despacho': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'pct_pagos_pensiones': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'pct_crecimiento_viviendas': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'pct_cartera_base': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pct_cartera_urbano': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pct_cartera_rural': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pct_eficiencia_recaudo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'gasto_sev_ppto_nc': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'sgr_presupuesto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'gasto_sev_sgr': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pct_pagos_sin_sgr': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'pct_pagos_sgr': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'reservas_presupuestales_nc': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cuentas_por_pagar_nc': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'superavit_fiscal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'recaudo_oleoductos_anio_n3': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'recaudo_oleoductos_anio_n2': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'recaudo_oleoductos_anio_n1': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'icld_calculado': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pct_icld_adicional_concejo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            # === GASTOS ===
            'pct_incremento_salarial': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'subsidio_transporte_mensual': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pct_aporte_pension': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'pct_aporte_salud': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'pct_aporte_arl': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.00001'}),
            'pct_cesantias': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'pct_intereses_cesantias': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'pct_prima_servicios': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'pct_prima_navidad': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'pct_prima_vacaciones': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'pct_bonif_servicios_prestados': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'pct_bonif_servicios_prestados_alto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'umbral_smlmv_bsp': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pct_bonif_recreacion': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'pct_aporte_sena': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'pct_aporte_icbf': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'pct_aporte_caja': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'pct_aporte_esap': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'pct_aporte_escuelas': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'pct_incremento_pensionados': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'tcr_deuda': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'pct_limite_intereses_ley358': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pct_limite_saldo_deuda_ley358': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pct_limite_funcionamiento_ley617': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


W = 'form-control'


class TablaConcejoPersoneriaForm(forms.ModelForm):
    class Meta:
        model = TablaConcejoPersoneria
        fields = '__all__'
        widgets = {
            'categoria': forms.Select(attrs={'class': W}),
            'valor_sesion_concejal': forms.NumberInput(attrs={'class': W, 'step': '0.01'}),
            'honorario_concejal_smlmv': forms.NumberInput(attrs={'class': W, 'step': '0.01'}),
            'sesiones_ordinarias': forms.NumberInput(attrs={'class': W}),
            'sesiones_extraordinarias': forms.NumberInput(attrs={'class': W}),
            'num_concejales': forms.NumberInput(attrs={'class': W}),
            'limite_concejo_pct_icld': forms.NumberInput(attrs={'class': W, 'step': '0.01'}),
            'limite_personeria_pct_icld': forms.NumberInput(attrs={'class': W, 'step': '0.01'}),
            'personeria_smlv_fijo': forms.NumberInput(attrs={'class': W}),
        }


class VigenciaFuturaForm(forms.ModelForm):
    class Meta:
        model = VigenciaFutura
        fields = '__all__'
        widgets = {
            'vigencia': forms.NumberInput(attrs={'class': W}),
            'vigencia_futura': forms.NumberInput(attrs={'class': W}),
            'descripcion': forms.Textarea(attrs={'class': W, 'rows': 2}),
            'codigo_fuente': forms.TextInput(attrs={'class': W}),
            'nombre_fuente': forms.TextInput(attrs={'class': W}),
            'valor': forms.NumberInput(attrs={'class': W, 'step': '0.01'}),
            'estado': forms.Select(attrs={'class': W}),
            'observaciones': forms.Textarea(attrs={'class': W, 'rows': 2}),
        }
