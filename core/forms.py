from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import ParametrosSistema


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
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
