from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from empresas.models import Matriz


class ApresentacaoProduto(models.Model):
    class Tipo(models.TextChoices):
        POTE = 'POTE', 'Pote'
        REFIL = 'REFIL', 'Refil flexivel'
        OUTRA = 'OUTRA', 'Outra'

    matriz = models.ForeignKey(Matriz, on_delete=models.PROTECT, related_name='apresentacoes_logisticas')
    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    largura_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], null=True, blank=True)
    altura_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], null=True, blank=True)
    profundidade_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], null=True, blank=True)
    ativo = models.BooleanField(default=True)
    observacoes = models.TextField(blank=True, default='')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['matriz', 'nome'], name='uniq_apresentacao_nome_matriz')]

    def clean(self):
        super().clean()
        if self.tipo == self.Tipo.REFIL and self.profundidade_cm is not None:
            raise ValidationError({'profundidade_cm': 'Refil flexivel nao possui profundidade rigida.'})
        if self.tipo == self.Tipo.REFIL and ((self.largura_cm is None) != (self.altura_cm is None)):
            raise ValidationError('Informe largura e altura juntas, ou deixe ambas vazias quando nao conhecidas.')

    def __str__(self):
        return self.nome


class ModeloCaixaExpedicao(models.Model):
    matriz = models.ForeignKey(Matriz, on_delete=models.PROTECT, related_name='modelos_caixa_expedicao')
    nome = models.CharField(max_length=100)
    largura_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    altura_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    comprimento_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    peso_maximo_gramas = models.PositiveIntegerField(null=True, blank=True)
    fornecedor = models.CharField(max_length=150, blank=True, default='')
    classificacao = models.CharField(max_length=60, blank=True, default='')
    observacoes = models.TextField(blank=True, default='')
    ativo = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['matriz', 'nome'], name='uniq_caixa_nome_matriz')]

    def __str__(self):
        return self.nome


class CapacidadeReferenciaCaixa(models.Model):
    matriz = models.ForeignKey(Matriz, on_delete=models.PROTECT, related_name='capacidades_logisticas')
    caixa = models.ForeignKey(ModeloCaixaExpedicao, on_delete=models.CASCADE, related_name='capacidades')
    apresentacao = models.ForeignKey(ApresentacaoProduto, on_delete=models.CASCADE, related_name='capacidades')
    quantidade = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    orientacao = models.CharField(max_length=60, blank=True, default='')
    descricao_original = models.CharField(max_length=250, blank=True, default='')
    observacoes = models.TextField(blank=True, default='')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['caixa', 'apresentacao'], name='uniq_capacidade_caixa_apresentacao')]

    def clean(self):
        super().clean()
        if self.caixa_id and self.apresentacao_id and self.matriz_id:
            if self.caixa.matriz_id != self.matriz_id or self.apresentacao.matriz_id != self.matriz_id:
                raise ValidationError('Caixa, apresentacao e capacidade devem pertencer a mesma matriz.')

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class ReferenciaCapacidadeRefil(models.Model):
    """Referência da aba de refis; NÃO é uma caixa de papelão de expedição."""
    matriz = models.ForeignKey(Matriz, on_delete=models.PROTECT, related_name='referencias_refis')
    refil = models.ForeignKey(ApresentacaoProduto, on_delete=models.CASCADE, related_name='referencias_capacidade')
    apresentacao_original = models.CharField(max_length=250)
    quantidade = models.PositiveIntegerField(null=True, blank=True)
    quantidade_original = models.CharField(max_length=30, blank=True, default='')
    fornecedor = models.CharField(max_length=150, blank=True, default='')
    observacoes = models.TextField(blank=True, default='')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['refil', 'apresentacao_original'], name='uniq_refil_tipo_referencia')]

    def clean(self):
        super().clean()
        if self.refil_id and self.matriz_id:
            if self.refil.matriz_id != self.matriz_id or self.refil.tipo != ApresentacaoProduto.Tipo.REFIL:
                raise ValidationError('A referencia deve pertencer a um refil da mesma matriz.')

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.refil} / {self.apresentacao_original}'


class RegistroFonteLogistica(models.Model):
    """Registro editável de todas as células não vazias da planilha de origem."""
    matriz = models.ForeignKey(Matriz, on_delete=models.PROTECT, related_name='fontes_logisticas')
    aba = models.CharField(max_length=100)
    linha = models.PositiveIntegerField()
    celulas = models.JSONField(default=dict)
    observacoes = models.TextField(blank=True, default='')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['matriz', 'aba', 'linha'], name='uniq_fonte_logistica_matriz_aba_linha')]

    def __str__(self):
        return f'{self.aba} / linha {self.linha}'


class AuditoriaCadastroLogistico(models.Model):
    matriz = models.ForeignKey(Matriz, on_delete=models.PROTECT, related_name='auditorias_logisticas')
    usuario = models.ForeignKey(__import__('django.conf',fromlist=['settings']).settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    tipo = models.CharField(max_length=40)
    objeto_id = models.PositiveIntegerField()
    acao = models.CharField(max_length=20)
    antes = models.JSONField(default=dict)
    depois = models.JSONField(default=dict)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em', '-pk']
