import uuid

from django.db import models
from django.db.models import Q

from empresas.models import Matriz, Loja


class Cliente(models.Model):

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.CASCADE,
        related_name='clientes'
    )

    loja_cadastro = models.ForeignKey(
        Loja,
        on_delete=models.PROTECT,
        related_name='clientes_cadastrados'
    )

    nome = models.CharField(max_length=150)

    cpf = models.CharField(max_length=14,
        db_index=True, blank=True)

    TIPO_PESSOA_PF = "PF"
    TIPO_PESSOA_PJ = "PJ"
    TIPO_PESSOA_CHOICES = (
        (TIPO_PESSOA_PF, "Pessoa Física"),
        (TIPO_PESSOA_PJ, "Pessoa Jurídica"),
    )

    tipo_pessoa = models.CharField(
        max_length=2,
        choices=TIPO_PESSOA_CHOICES,
        default=TIPO_PESSOA_PF,
    )
    cnpj = models.CharField(max_length=18, blank=True, default="")
    cnpj_normalizado = models.CharField(
        max_length=14,
        blank=True,
        default="",
        db_index=True,
    )
    razao_social = models.CharField(max_length=150, blank=True, default="")
    nome_fantasia = models.CharField(max_length=150, blank=True, default="")
    inscricao_estadual = models.CharField(max_length=30, blank=True, default="")
    contato_responsavel = models.CharField(max_length=150, blank=True, default="")

    cep = models.CharField(max_length=8, blank=True, default="")
    logradouro = models.CharField(max_length=150, blank=True, default="")
    numero = models.CharField(max_length=20, blank=True, default="")
    complemento = models.CharField(max_length=100, blank=True, default="")
    bairro = models.CharField(max_length=100, blank=True, default="")
    cidade = models.CharField(max_length=100, blank=True, default="")
    uf = models.CharField(max_length=2, blank=True, default="")
    telefone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        db_index=True
    )

    cpf_normalizado = models.CharField(
    max_length=11,
    db_index=True,
    blank=True
)

    telefone_normalizado = models.CharField(
        max_length=20,
        db_index=True,
        blank=True
    )

    data_nascimento = models.DateField(
        blank=True,
        null=True,
        db_index=True
    )

    email = models.EmailField(
        blank=True,
        null=True,
        db_index=True
    )

    nome_normalizado = models.CharField(
        max_length=150,
        db_index=True,
        blank=True
    )

    email_normalizado = models.EmailField(
        db_index=True,
        blank=True
    )

    aceita_email = models.BooleanField(default=True)
    aceita_sms = models.BooleanField(default=False)

    ativo = models.BooleanField(default=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome']

        constraints = [
            models.UniqueConstraint(
                fields=['matriz', 'cpf_normalizado'],
                condition=Q(tipo_pessoa='PF') & ~Q(cpf_normalizado=''),
                name='unique_cliente_pf_por_matriz_cpf_norm',
            ),
            models.UniqueConstraint(
                fields=['matriz', 'cnpj_normalizado'],
                condition=Q(tipo_pessoa='PJ') & ~Q(cnpj_normalizado=''),
                name='unique_cliente_pj_por_matriz_cnpj_norm',
            ),
        ]

        indexes = [
            models.Index(fields=['matriz', 'cpf']),
            models.Index(fields=['matriz', 'cpf_normalizado']),
            models.Index(fields=['matriz', 'telefone_normalizado']),
            models.Index(fields=['matriz', 'nome']),
            models.Index(fields=['matriz', 'telefone']),
            models.Index(fields=['matriz', 'email']),
            models.Index(fields=['matriz', 'data_nascimento']),
            models.Index(fields=['matriz', 'ativo']),
            models.Index(fields=['loja_cadastro', 'criado_em']),
            models.Index(fields=['matriz', 'nome_normalizado']),
            models.Index(fields=['matriz', 'email_normalizado']),
        ]

    @staticmethod
    def _documento_valido(numero, pesos_primeiro, pesos_segundo):
        if not numero or len(set(numero)) == 1:
            return False

        def calcular(base, pesos):
            soma = sum(int(digito) * peso for digito, peso in zip(base, pesos))
            resto = soma % 11
            return '0' if resto < 2 else str(11 - resto)

        primeiro = calcular(numero[:-2], pesos_primeiro)
        segundo = calcular(numero[:-2] + primeiro, pesos_segundo)
        return numero[-2:] == primeiro + segundo

    def clean(self):
        super().clean()
        from django.core.exceptions import ValidationError
        from .utils import limpar_numero

        erros = {}
        consumidor_tecnico = (
            (self.nome or '').strip().upper() == 'CONSUMIDOR'
            and (self.cpf or '').strip().upper() == 'CONSUMIDOR'
        )

        if consumidor_tecnico:
            return

        if self.tipo_pessoa == self.TIPO_PESSOA_PF:
            if not (self.nome or '').strip():
                erros['nome'] = 'Nome é obrigatório para pessoa física.'

            cpf = limpar_numero(self.cpf)
            if not cpf:
                erros['cpf'] = 'CPF é obrigatório para pessoa física.'
            elif len(cpf) != 11:
                erros['cpf'] = 'CPF deve conter 11 números.'
            elif not self._documento_valido(
                cpf,
                [10, 9, 8, 7, 6, 5, 4, 3, 2],
                [11, 10, 9, 8, 7, 6, 5, 4, 3, 2],
            ):
                erros['cpf'] = 'CPF informado é inválido.'

            if not erros.get('cpf') and self.matriz_id:
                duplicado_pf = type(self).objects.filter(
                    matriz_id=self.matriz_id,
                    cpf_normalizado=cpf,
                )
                if self.pk:
                    duplicado_pf = duplicado_pf.exclude(pk=self.pk)
                if duplicado_pf.exists():
                    erros['cpf'] = 'Já existe um cliente com este CPF nesta matriz.'

        elif self.tipo_pessoa == self.TIPO_PESSOA_PJ:
            if not (self.razao_social or '').strip():
                erros['razao_social'] = 'Razão social é obrigatória para pessoa jurídica.'

            cnpj = limpar_numero(self.cnpj)
            if not cnpj:
                erros['cnpj'] = 'CNPJ é obrigatório para pessoa jurídica.'
            elif len(cnpj) != 14:
                erros['cnpj'] = 'CNPJ deve conter 14 números.'
            elif not self._documento_valido(
                cnpj,
                [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2],
                [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2],
            ):
                erros['cnpj'] = 'CNPJ informado é inválido.'

            if not erros.get('cnpj') and self.matriz_id:
                duplicado = type(self).objects.filter(
                    matriz_id=self.matriz_id,
                    cnpj_normalizado=cnpj,
                )
                if self.pk:
                    duplicado = duplicado.exclude(pk=self.pk)
                if duplicado.exists():
                    erros['cnpj'] = 'Já existe um cliente com este CNPJ nesta matriz.'

        if erros:
            raise ValidationError(erros)

    def save(self, *args, **kwargs):
        from .utils import normalizar_texto, limpar_numero

        if self.tipo_pessoa == self.TIPO_PESSOA_PJ:
            self.cpf = ""
            self.cpf_normalizado = ""
            self.data_nascimento = None
        elif self.tipo_pessoa == self.TIPO_PESSOA_PF:
            self.razao_social = ""
            self.nome_fantasia = ""
            self.cnpj = ""
            self.cnpj_normalizado = ""
            self.inscricao_estadual = ""
            self.contato_responsavel = ""

        self.nome_normalizado = normalizar_texto(self.nome)
        self.email_normalizado = normalizar_texto(self.email)
        self.cpf_normalizado = limpar_numero(self.cpf)
        self.cnpj_normalizado = limpar_numero(self.cnpj)
        self.telefone_normalizado = limpar_numero(self.telefone)

        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.nome} - {self.cpf}'
