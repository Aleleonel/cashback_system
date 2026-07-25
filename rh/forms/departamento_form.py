from django import forms

from rh.models import Departamento


class DepartamentoForm(forms.ModelForm):
    class Meta:
        model = Departamento

        fields = [
            "matriz",
            "nome",
            "descricao",
            "ativo",
        ]

        widgets = {
            "descricao": forms.Textarea(
                attrs={
                    "rows": 4,
                    "class": "form-control",
                }
            ),
            "nome": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "maxlength": 100,
                    "autocomplete": "off",
                }
            ),
            "matriz": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "ativo": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

    def clean_nome(self):
        nome = self.cleaned_data["nome"].strip()

        if not nome:
            raise forms.ValidationError(
                "Informe o nome do departamento."
            )

        return nome

    def save(self, commit=True):
        self.instance.nome = self.cleaned_data["nome"].strip()
        self.instance.descricao = self.cleaned_data.get(
            "descricao",
            "",
        ).strip()

        return super().save(commit=commit)