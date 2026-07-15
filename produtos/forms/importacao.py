from pathlib import Path

from django import forms

from core.forms import BootstrapForm


class ImportarProdutosForm(BootstrapForm):
    arquivo = forms.FileField(
        label='Planilha de produtos',
        widget=forms.ClearableFileInput(attrs={
            'accept': '.xlsx,.xls',
        })
    )

    def clean_arquivo(self):
        arquivo = self.cleaned_data['arquivo']

        extensao = Path(
            arquivo.name
        ).suffix.lower()

        extensoes_permitidas = {
            '.xlsx',
            '.xls',
        }

        if extensao not in extensoes_permitidas:
            raise forms.ValidationError(
                'Envie uma planilha Excel nos formatos .xlsx ou .xls.'
            )

        limite_bytes = 10 * 1024 * 1024

        if arquivo.size > limite_bytes:
            raise forms.ValidationError(
                'A planilha deve possuir no máximo 10 MB.'
            )

        return arquivo
