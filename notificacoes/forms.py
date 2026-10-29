from django import forms
from empresas.models import Loja
from .models import AvisoInterno


class AvisoInternoForm(forms.ModelForm):
    class Meta:
        model = AvisoInterno
        fields = ("titulo", "mensagem", "prioridade", "inicio_exibicao", "fim_exibicao", "loja", "ativo")
        widgets = {
            "titulo": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ex.: Fechamento do caixa às 21h",
                "autocomplete": "off",
            }),
            "mensagem": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Escreva uma orientação curta e objetiva para a equipe.",
            }),
            "prioridade": forms.Select(attrs={"class": "form-select"}),
            "inicio_exibicao": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"},
                format="%Y-%m-%dT%H:%M",
            ),
            "fim_exibicao": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"},
                format="%Y-%m-%dT%H:%M",
            ),
            "loja": forms.Select(attrs={"class": "form-select"}),
            "ativo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, matriz=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["inicio_exibicao"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["fim_exibicao"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["loja"].queryset = Loja.objects.filter(matriz=matriz) if matriz else Loja.objects.none()
        self.fields["loja"].empty_label = "Toda a matriz"