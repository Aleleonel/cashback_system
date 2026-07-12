from django.db import IntegrityError

from cashback.models import LancamentoCashback

from .resultados import ResultadoOperacaoVenda
from .venda import registrar_venda


def executar_venda_idempotente(
    *,
    matriz,
    loja,
    usuario,
    chave_idempotencia,
    cpf,
    nome,
    valor_compra,
    valor_cashback_usado=0,
    aplicar_voucher=False,
    codigo_voucher='',
    telefone='',
    email='',
    data_nascimento=None,
    aceita_email=True,
    aceita_sms=False,
    observacao='',
):
    try:
        resultado = registrar_venda(
            matriz=matriz,
            loja=loja,
            usuario=usuario,
            chave_idempotencia=chave_idempotencia,
            cpf=cpf,
            nome=nome,
            telefone=telefone,
            email=email,
            data_nascimento=data_nascimento,
            valor_compra=valor_compra,
            valor_cashback_usado=valor_cashback_usado,
            aceita_email=aceita_email,
            aceita_sms=aceita_sms,
            observacao=observacao,
            aplicar_voucher=aplicar_voucher,
            codigo_voucher=codigo_voucher,
        )

        return ResultadoOperacaoVenda(
            compra=resultado['compra'],
            cliente=resultado['cliente'],
            uso_voucher=resultado['uso_voucher'],
            beneficios=resultado['beneficios'],
            duplicada=resultado['duplicada'],
        )

    except IntegrityError:
        lancamento_existente = (
            LancamentoCashback.objects
            .filter(
                matriz=matriz,
                chave_idempotencia=chave_idempotencia,
            )
            .select_related(
                'cliente',
            )
            .first()
        )

        if lancamento_existente is None:
            raise

        return ResultadoOperacaoVenda(
            compra=lancamento_existente,
            cliente=lancamento_existente.cliente,
            uso_voucher=None,
            beneficios=None,
            duplicada=True,
        )
