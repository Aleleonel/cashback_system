from django import forms
from core.forms import BootstrapModelForm
from produtos.models.logistica import ApresentacaoProduto, ModeloCaixaExpedicao, CapacidadeReferenciaCaixa, ReferenciaCapacidadeRefil, RegistroFonteLogistica

class ApresentacaoLogisticaForm(BootstrapModelForm):
    class Meta:
        model = ApresentacaoProduto
        fields = ['nome', 'tipo', 'largura_cm', 'altura_cm', 'profundidade_cm', 'observacoes', 'ativo']

class CaixaExpedicaoForm(BootstrapModelForm):
    class Meta:
        model = ModeloCaixaExpedicao
        fields = ['nome', 'largura_cm', 'altura_cm', 'comprimento_cm', 'peso_maximo_gramas', 'fornecedor', 'classificacao', 'observacoes', 'ativo']

class CapacidadeCaixaForm(BootstrapModelForm):
    class Meta:
        model = CapacidadeReferenciaCaixa
        fields = ['caixa', 'apresentacao', 'quantidade', 'orientacao', 'descricao_original', 'observacoes']

    def __init__(self, *args, matriz, **kwargs):
        super().__init__(*args, **kwargs)
        self.matriz = matriz
        self.fields['caixa'].queryset = ModeloCaixaExpedicao.objects.filter(matriz=matriz)
        self.fields['apresentacao'].queryset = ApresentacaoProduto.objects.filter(matriz=matriz)

    def clean(self):
        data = super().clean()
        caixa, apresentacao = data.get('caixa'), data.get('apresentacao')
        if caixa and apresentacao and (caixa.matriz_id != self.matriz.pk or apresentacao.matriz_id != self.matriz.pk):
            raise forms.ValidationError('Caixa e apresentacao devem pertencer a matriz atual.')
        return data


class ReferenciaCapacidadeRefilForm(BootstrapModelForm):
    class Meta:
        model = ReferenciaCapacidadeRefil
        fields = ['refil', 'apresentacao_original', 'quantidade', 'quantidade_original', 'fornecedor', 'observacoes']

    def __init__(self, *args, matriz, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['refil'].queryset = ApresentacaoProduto.objects.filter(matriz=matriz, tipo='REFIL')


class RegistroFonteLogisticaForm(BootstrapModelForm):
    class Meta:
        model = RegistroFonteLogistica
        fields = ['aba', 'linha', 'celulas', 'observacoes']
