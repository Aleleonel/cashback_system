import secrets
import string

from django.core.exceptions import ValidationError
from django.db.models import F

from django.db import transaction
from django.utils import timezone

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria

from .models import (
    Voucher, 
    VoucherLoja,
    UsoVoucher,
)

# ==========================================================
# GERAÇÃO DE CÓDIGO
# ==========================================================

CARACTERES_CODIGO = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'


def gerar_codigo_voucher():

    ano = timezone.localdate().strftime('%y')

    while True:

        codigo = (
            f'VCH-{ano}-'
            f'{"".join(secrets.choice(CARACTERES_CODIGO) for _ in range(6))}'
        )

        if not Voucher.objects.filter(codigo=codigo).exists():
            return codigo


# ==========================================================
# CRUD
# ==========================================================

@transaction.atomic
def criar_voucher(
    *,
    matriz,
    dados,
    usuario_executor,
    request=None,
):

    voucher = Voucher.objects.create(
        matriz=matriz,
        cliente=dados.get('cliente'),
        codigo=gerar_codigo_voucher(),
        nome=dados['nome'],
        descricao=dados.get('descricao', ''),
        tipo=dados['tipo'],
        origem=Voucher.Origem.MANUAL,
        valor=dados.get('valor'),
        percentual=dados.get('percentual'),
        data_inicio=dados['data_inicio'],
        data_fim=dados['data_fim'],
        uso_unico_por_cliente=dados['uso_unico_por_cliente'],
        limite_utilizacao=dados['limite_utilizacao'],
    )

    lojas = dados.get('lojas')

    if lojas:
        VoucherLoja.objects.bulk_create([
            VoucherLoja(
                voucher=voucher,
                loja=loja
            )
            for loja in lojas
        ])


    registrar_auditoria(
        usuario=usuario_executor,
        matriz=matriz,
        loja=None,
        acao=RegistroAuditoria.ACAO_CRIAR,
        recurso='voucher',
        recurso_id=voucher.id,
        descricao=f'Voucher criado: {voucher.codigo}',
        request=request,
    )

    return voucher


@transaction.atomic
def editar_voucher(
    *,
    voucher,
    dados,
    usuario_executor,
    request=None,
):

    voucher.cliente = dados.get('cliente')
    voucher.nome = dados['nome']
    voucher.descricao = dados.get('descricao', '')
    voucher.tipo = dados['tipo']
    voucher.valor = dados.get('valor')
    voucher.percentual = dados.get('percentual')
    voucher.data_inicio = dados['data_inicio']
    voucher.data_fim = dados['data_fim']
    voucher.uso_unico_por_cliente = dados['uso_unico_por_cliente']
    voucher.limite_utilizacao = dados['limite_utilizacao']

    voucher.save()

    lojas = dados.get('lojas')

    voucher.lojas_permitidas.all().delete()

    if lojas:
        VoucherLoja.objects.bulk_create([
            VoucherLoja(
                voucher=voucher,
                loja=loja
            )
            for loja in lojas
        ])

    registrar_auditoria(
        usuario=usuario_executor,
        matriz=voucher.matriz,
        loja=None,
        acao=RegistroAuditoria.ACAO_EDITAR,
        recurso='voucher',
        recurso_id=voucher.id,
        descricao=f'Voucher alterado: {voucher.codigo}',
        request=request,
    )

    return voucher


# ==========================================================
# STATUS
# ==========================================================

@transaction.atomic
def ativar_voucher(
    *,
    voucher,
    usuario_executor,
    request=None,
):

    voucher.status = Voucher.Status.ATIVO
    voucher.save(update_fields=['status'])

    registrar_auditoria(
        usuario=usuario_executor,
        matriz=voucher.matriz,
        loja=None,
        acao=RegistroAuditoria.ACAO_EDITAR,
        recurso='voucher',
        recurso_id=voucher.id,
        descricao=f'Voucher ativado: {voucher.codigo}',
        request=request,
    )


@transaction.atomic
def inativar_voucher(
    *,
    voucher,
    usuario_executor,
    request=None,
):

    voucher.status = Voucher.Status.INATIVO
    voucher.save(update_fields=['status'])

    registrar_auditoria(
        usuario=usuario_executor,
        matriz=voucher.matriz,
        loja=None,
        acao=RegistroAuditoria.ACAO_EDITAR,
        recurso='voucher',
        recurso_id=voucher.id,
        descricao=f'Voucher inativado: {voucher.codigo}',
        request=request,
    )


# ==========================================================
# VALIDAÇÃO
# ==========================================================

def validar_voucher(*, voucher):

    if not voucher.esta_ativo:
        return False, 'Voucher inativo.'

    if voucher.ainda_nao_iniciado:
        return False, 'Voucher ainda não está vigente.'

    if voucher.esta_expirado:
        return False, 'Voucher expirado.'

    if voucher.esta_esgotado:
        return False, 'Voucher sem utilizações disponíveis.'

    return True, ''


# ==========================================================
# UTILIZAÇÃO
# ==========================================================

def utilizar_voucher():
    """
    Implementação prevista para Sprint 16C.
    """
    raise NotImplementedError()


def cancelar_utilizacao():
    """
    Implementação prevista para Sprint 16C.
    """
    raise NotImplementedError()


@transaction.atomic
def registrar_uso_voucher(
    *,
    matriz,
    loja,
    cliente,
    voucher,
    usuario,
    compra,
    valor_compra,
    valor_desconto,
    observacao='',
):
    voucher_bloqueado = Voucher.objects.select_for_update().get(
        id=voucher.id,
        matriz=matriz
    )

    valido, mensagem = validar_voucher(
        voucher=voucher_bloqueado
    )

    if not valido:
        raise ValidationError(mensagem)

    if voucher_bloqueado.total_utilizado >= voucher_bloqueado.limite_utilizacao:
        raise ValidationError(
            'Voucher sem utilizações disponíveis.'
        )

    lojas_permitidas = voucher_bloqueado.lojas_permitidas.all()

    if lojas_permitidas.exists():
        permitido = lojas_permitidas.filter(
            loja=loja
        ).exists()

        if not permitido:
            raise ValidationError(
                'Este voucher não é válido para esta loja.'
            )

    uso = UsoVoucher.objects.create(
        matriz=matriz,
        loja=loja,
        cliente=cliente,
        voucher=voucher_bloqueado,
        usuario=usuario,
        compra=compra,
        valor_compra=valor_compra,
        valor_desconto=valor_desconto,
        observacao=observacao,
    )

    Voucher.objects.filter(
        id=voucher_bloqueado.id,
        total_utilizado__lt=F('limite_utilizacao')
    ).update(
        total_utilizado=F('total_utilizado') + 1
    )

    return uso