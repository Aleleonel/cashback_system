from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria
from estoque.choices import StatusReservaEstoque
from estoque.models import ReservaEstoque
from estoque.selectors import get_saldo_disponivel
from produtos.models import Produto

from .resultados import ResultadoReservaEstoque


def registrar_reserva_estoque(
    *,
    matriz,
    loja,
    produto,
    origem,
    quantidade,
    chave_idempotencia,
    usuario=None,
    documento_referencia='',
    origem_id='',
    expira_em=None,
    request=None,
):
    chave_idempotencia = _normalizar_chave_idempotencia(
        chave_idempotencia
    )

    quantidade = _normalizar_quantidade(quantidade)

    documento_referencia = _normalizar_texto(
        documento_referencia
    )
    origem_id = _normalizar_texto(origem_id)

    _validar_contexto(
        matriz=matriz,
        loja=loja,
        produto=produto,
    )

    resultado_idempotente = _resolver_idempotencia(
        matriz=matriz,
        loja=loja,
        produto=produto,
        origem=origem,
        quantidade=quantidade,
        chave_idempotencia=chave_idempotencia,
        documento_referencia=documento_referencia,
        origem_id=origem_id,
        expira_em=expira_em,
    )

    if resultado_idempotente is not None:
        return resultado_idempotente

    try:
        return _registrar_reserva_estoque_atomic(
            matriz=matriz,
            loja=loja,
            produto=produto,
            origem=origem,
            quantidade=quantidade,
            chave_idempotencia=chave_idempotencia,
            usuario=usuario,
            documento_referencia=documento_referencia,
            origem_id=origem_id,
            expira_em=expira_em,
            request=request,
        )

    except IntegrityError:
        resultado_idempotente = _resolver_idempotencia(
            matriz=matriz,
            loja=loja,
            produto=produto,
            origem=origem,
            quantidade=quantidade,
            chave_idempotencia=chave_idempotencia,
            documento_referencia=documento_referencia,
            origem_id=origem_id,
            expira_em=expira_em,
        )

        if resultado_idempotente is None:
            raise

        return resultado_idempotente


@transaction.atomic
def _registrar_reserva_estoque_atomic(
    *,
    matriz,
    loja,
    produto,
    origem,
    quantidade,
    chave_idempotencia,
    usuario=None,
    documento_referencia='',
    origem_id='',
    expira_em=None,
    request=None,
):
    _bloquear_contexto_reserva(
        produto=produto
    )

    resultado_idempotente = _resolver_idempotencia(
        matriz=matriz,
        loja=loja,
        produto=produto,
        origem=origem,
        quantidade=quantidade,
        chave_idempotencia=chave_idempotencia,
        documento_referencia=documento_referencia,
        origem_id=origem_id,
        expira_em=expira_em,
    )

    if resultado_idempotente is not None:
        return resultado_idempotente

    saldo_disponivel = get_saldo_disponivel(
        matriz=matriz,
        loja=loja,
        produto=produto,
    )

    _validar_saldo_disponivel(
        saldo_disponivel=saldo_disponivel,
        quantidade=quantidade,
    )

    reserva = ReservaEstoque.objects.create(
        matriz=matriz,
        loja=loja,
        produto=produto,
        quantidade=quantidade,
        status=StatusReservaEstoque.ATIVA,
        origem=origem,
        origem_id=origem_id,
        chave_idempotencia=chave_idempotencia,
        documento_referencia=documento_referencia,
        usuario=usuario,
        expira_em=expira_em,
    )

    _registrar_auditoria_reserva(
        usuario=usuario,
        matriz=matriz,
        loja=loja,
        produto=produto,
        quantidade=quantidade,
        saldo_disponivel_anterior=saldo_disponivel,
        reserva=reserva,
        request=request,
    )

    return ResultadoReservaEstoque(
        reserva=reserva,
        duplicada=False,
    )


def _normalizar_chave_idempotencia(chave_idempotencia):
    chave_idempotencia = _normalizar_texto(
        chave_idempotencia
    )

    if not chave_idempotencia:
        raise ValidationError({
            'chave_idempotencia': (
                'A chave de idempot?ncia ? obrigat?ria.'
            )
        })

    return chave_idempotencia


def _normalizar_texto(valor):
    return (
        valor or ''
    ).strip()


def _normalizar_quantidade(quantidade):
    try:
        quantidade = Decimal(str(quantidade))

        if not quantidade.is_finite():
            raise InvalidOperation

        quantidade = quantidade.quantize(
            Decimal('0.001')
        )

    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError({
            'quantidade': (
                'Informe uma quantidade v?lida.'
            )
        })

    if quantidade <= Decimal('0.000'):
        raise ValidationError({
            'quantidade': (
                'A quantidade deve ser maior que zero.'
            )
        })

    return quantidade


def _validar_contexto(
    *,
    matriz,
    loja,
    produto,
):
    erros = {}

    if loja.matriz_id != matriz.id:
        erros['loja'] = (
            'A loja deve pertencer ? matriz informada.'
        )

    if produto.matriz_id != matriz.id:
        erros['produto'] = (
            'O produto deve pertencer ? matriz informada.'
        )

    if not produto.controla_estoque:
        erros['produto'] = (
            'O produto informado n?o controla estoque.'
        )

    if erros:
        raise ValidationError(erros)


def _resolver_idempotencia(
    *,
    matriz,
    loja,
    produto,
    origem,
    quantidade,
    chave_idempotencia,
    documento_referencia,
    origem_id,
    expira_em,
):
    reserva = _buscar_reserva_idempotente(
        matriz=matriz,
        chave_idempotencia=chave_idempotencia,
    )

    if reserva is None:
        return None

    _validar_reprocessamento_idempotente(
        reserva=reserva,
        loja=loja,
        produto=produto,
        origem=origem,
        quantidade=quantidade,
        documento_referencia=documento_referencia,
        origem_id=origem_id,
        expira_em=expira_em,
    )

    return ResultadoReservaEstoque(
        reserva=reserva,
        duplicada=True,
    )


def _buscar_reserva_idempotente(
    *,
    matriz,
    chave_idempotencia,
):
    return (
        ReservaEstoque.objects
        .filter(
            matriz=matriz,
            chave_idempotencia=chave_idempotencia,
        )
        .select_related(
            'matriz',
            'loja',
            'produto',
        )
        .first()
    )


def _validar_reprocessamento_idempotente(
    *,
    reserva,
    loja,
    produto,
    origem,
    quantidade,
    documento_referencia,
    origem_id,
    expira_em,
):
    campos_compativeis = (
        reserva.loja_id == loja.pk
        and reserva.produto_id == produto.pk
        and reserva.origem == origem
        and reserva.quantidade == quantidade
        and (
            reserva.documento_referencia
            == documento_referencia
        )
        and reserva.origem_id == origem_id
        and reserva.expira_em == expira_em
    )

    if not campos_compativeis:
        raise ValidationError({
            'chave_idempotencia': (
                'A chave de idempot?ncia j? foi utilizada '
                'por uma opera??o diferente.'
            )
        })


def _bloquear_contexto_reserva(*, produto):
    Produto.objects.select_for_update().get(
        pk=produto.pk
    )


def _validar_saldo_disponivel(
    *,
    saldo_disponivel,
    quantidade,
):
    if quantidade > saldo_disponivel:
        raise ValidationError({
            'quantidade': (
                'O saldo dispon?vel ? insuficiente '
                'para esta reserva.'
            )
        })


def _registrar_auditoria_reserva(
    *,
    usuario,
    matriz,
    loja,
    produto,
    quantidade,
    saldo_disponivel_anterior,
    reserva,
    request,
):
    saldo_disponivel_posterior = (
        saldo_disponivel_anterior - quantidade
    )

    registrar_auditoria(
        usuario=usuario,
        matriz=matriz,
        loja=loja,
        acao=RegistroAuditoria.ACAO_CRIAR,
        recurso='estoque.reserva',
        recurso_id=reserva.uuid,
        descricao=(
            f'Reserva de estoque: '
            f'produto={produto.codigo_interno}; '
            f'quantidade={quantidade}; '
            f'saldo_disponivel_anterior={saldo_disponivel_anterior}; '
            f'saldo_disponivel_posterior={saldo_disponivel_posterior}.'
        ),
        request=request,
    )
