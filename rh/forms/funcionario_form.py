import re

from django import forms

from rh.models import Funcionario


class FuncionarioForm(forms.ModelForm):
    class Meta:
        model = Funcionario

        fields = [
            "matriz",
            "nome_completo",
            "cpf",
            "rg",
            "email",
            "telefone",
            "data_nascimento",
            "data_admissao",
            "departamento",
            "cargo",
            "ativo",
        ]

        widgets = {
            "matriz": forms.Select(attrs={"class": "form-select"}),
            "nome_completo": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "maxlength": 150,
                    "autocomplete": "off",
                }
            ),
            "cpf": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "maxlength": 14,
                    "autocomplete": "off",
                }
            ),
            "rg": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "maxlength": 20,
                    "autocomplete": "off",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",
                }
            ),
            "telefone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "maxlength": 20,
                    "autocomplete": "off",
                }
            ),
            "data_nascimento": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "data_admissao": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "departamento": forms.Select(attrs={"class": "form-select"}),
            "cargo": forms.Select(attrs={"class": "form-select"}),
            "ativo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, matriz=None, **kwargs):
        super().__init__(*args, **kwargs)

        if matriz is not None:
            self.fields["matriz"].queryset = (
                self.fields["matriz"].queryset.filter(pk=matriz.pk)
            )
            self.fields["matriz"].initial = matriz
            self.fields["cargo"].queryset = (
                self.fields["cargo"].queryset.filter(
                    matriz=matriz,
                    ativo=True,
                )
            )
            self.fields["departamento"].queryset = (
                self.fields["departamento"].queryset.filter(
                    matriz=matriz,
                    ativo=True,
                )
            )

    def clean_nome_completo(self):
        nome = self.cleaned_data["nome_completo"].strip()

        if not nome:
            raise forms.ValidationError("Informe o nome completo.")

        return nome

    def clean_cpf(self):
        cpf = re.sub(r"\D", "", self.cleaned_data["cpf"])

        if len(cpf) != 11:
            raise forms.ValidationError("Informe um CPF com 11 dígitos.")

        return cpf

    def clean_rg(self):
        return self.cleaned_data.get("rg", "").strip()

    def clean_email(self):
        return self.cleaned_data.get("email", "").strip().lower()

    def clean_telefone(self):
        return self.cleaned_data.get("telefone", "").strip()

    def clean(self):
        cleaned_data = super().clean()

        matriz = cleaned_data.get("matriz")
        cargo = cleaned_data.get("cargo")
        departamento = cleaned_data.get("departamento")

        if matriz and cargo and cargo.matriz_id != matriz.id:
            self.add_error(
                "cargo",
                "O cargo selecionado não pertence à matriz informada.",
            )

        if matriz and departamento and departamento.matriz_id != matriz.id:
            self.add_error(
                "departamento",
                "O departamento selecionado não pertence à matriz informada.",
            )

        return cleaned_data