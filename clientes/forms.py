from django import forms

from .models import Cliente
from .validators import formatar_cpf


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = '__all__'
        widgets = {
            'cpf': forms.TextInput(attrs={'placeholder': '000.000.000-00', 'inputmode': 'numeric'}),
            'telefone': forms.TextInput(attrs={'placeholder': '(00) 00000-0000', 'inputmode': 'tel'}),
            'estado': forms.TextInput(attrs={'placeholder': 'SP', 'maxlength': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs.setdefault('class', 'form-control')

    def full_clean(self):
        super().full_clean()
        # Campos com erro ficam destacados e ligados à mensagem (leitores de tela).
        for nome in self.errors:
            if nome in self.fields:
                attrs = self.fields[nome].widget.attrs
                attrs['class'] = attrs.get('class', '') + ' is-invalid'
                attrs['aria-invalid'] = 'true'
                attrs['aria-describedby'] = f'id_{nome}-erro'

    def clean_cpf(self):
        # O validador do modelo confere os dígitos; aqui o CPF é gravado
        # sempre no mesmo formato, para que a regra de CPF único funcione
        # com ou sem pontuação.
        cpf = self.cleaned_data['cpf']
        return formatar_cpf(cpf) if len(''.join(c for c in cpf if c.isdigit())) == 11 else cpf

    def clean_estado(self):
        return self.cleaned_data['estado'].upper()
