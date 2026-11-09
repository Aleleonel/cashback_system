"""F32P3I: consolidacao nao fiscal de pedido atacado em sessao PDV.

Entrada programatica; endpoint HTTP e testes operacionais ainda pendentes.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from pdv.choices import ModalidadeComercial, StatusOperacaoVenda, TipoEmissaoVenda
from pdv.models import ItemVenda, SessaoCaixa, Venda
from pdv.services.vendas.caixa import registrar_movimentacao_caixa_venda
from pdv.services.vendas.auditoria import registrar_auditoria_finalizacao_venda
from pdv.services.vendas.fechamento import _registrar_pagamentos
from pdv.services.vendas.finalizacao import (
    _atribuir_numero_venda, _congelar_custo_itens,
    gerar_contas_receber_venda,
)
from pdv.services.vendas.validacoes import validar_venda_para_finalizacao
from .integracao_pdv import validar_contexto_consolidacao
from .integracao_itens_pdv import preparar_itens_pdv
from .models import PedidoAtacado, StatusPedidoAtacado, TipoEmissaoPedidoAtacado
from .order_services import _reservas_ativas_pedido
from estoque.services import confirmar_reserva_estoque


@transaction.atomic
def consolidar_pedido_atacado_pdv(*, pedido, sessao_caixa, operador, pagamentos, request=None):
    """Finaliza pedido e venda atomicamente, usando exclusivamente reservas do pedido.

    Somente operacoes NAO FISCAIS. Autorizacao HTTP e teste operacional sao obrigatorios
    antes de disponibilizar esta funcao na interface.
    """
    pedido = (PedidoAtacado.objects.select_for_update()
              .select_related('matriz', 'loja', 'cliente', 'vendedor')
              .get(pk=pedido.pk))
    if pedido.status == StatusPedidoAtacado.FINALIZADO and pedido.venda_pdv_id:
        venda = Venda.objects.get(pk=pedido.venda_pdv_id)
        if venda.status != StatusOperacaoVenda.FINALIZADA:
            raise ValidationError({'pedido': 'Vinculo inconsistente: venda nao finalizada.'})
        return venda
    if pedido.venda_pdv_id:
        raise ValidationError({'pedido': 'Pedido ja possui venda vinculada.'})
    if pedido.tipo_emissao != TipoEmissaoPedidoAtacado.NAO_FISCAL:
        raise ValidationError({'fiscal': 'Consolidacao fiscal exige fluxo fiscal especifico.'})
    if sessao_caixa is None:
        raise ValidationError({'sessao_caixa': 'Uma sessao de caixa aberta e obrigatoria.'})
    sessao = SessaoCaixa.objects.select_for_update().get(pk=sessao_caixa.pk)
    sessao = validar_contexto_consolidacao(
        pedido=pedido, sessao_caixa=sessao, operador=operador,
    )
    itens, ajustes = preparar_itens_pdv(pedido=pedido)
    if ajustes['total'] <= Decimal('0.00'):
        raise ValidationError({'total': 'O total da venda deve ser positivo.'})
    if not isinstance(pagamentos, list) or not pagamentos:
        raise ValidationError({'pagamentos': 'Informe os pagamentos da venda.'})

    venda = Venda.objects.create(
        matriz=pedido.matriz, loja=pedido.loja, cliente=pedido.cliente,
        vendedor=pedido.vendedor, operador=operador, sessao_caixa=sessao,
        modalidade=ModalidadeComercial.ATACADO,
        tipo_emissao=TipoEmissaoVenda.NAO_FISCAL,
        status=StatusOperacaoVenda.RASCUNHO,
        observacao=f'Consolidacao do pedido de atacado {pedido.pk}',
    )
    for dados in itens:
        ItemVenda.objects.create(
            venda=venda, produto_id=dados['produto_id'],
            sequencia=dados['sequencia'], quantidade=dados['quantidade'],
            preco_unitario=dados['preco_unitario'],
            desconto=dados['desconto'], acrescimo=dados['acrescimo'],
            subtotal=dados['subtotal'], total=dados['total'],
        )
    venda.desconto_geral = ajustes['desconto_geral']
    venda.acrescimo_geral = ajustes['acrescimo_geral']
    venda.recalcular_totais(salvar=False)
    if venda.total != ajustes['total']:
        raise ValidationError({'total': 'Divergencia de total entre pedido e PDV.'})
    venda.save(update_fields=['desconto_geral', 'acrescimo_geral', 'subtotal',
                              'desconto', 'acrescimo', 'total', 'quantidade_itens', 'atualizada_em'])
    _registrar_pagamentos(venda, pagamentos)
    validar_venda_para_finalizacao(venda=venda, permitir_fiscal=False)
    _congelar_custo_itens(venda=venda)

    # Confirmar SOMENTE reservas criadas pelo pedido atacado.
    reservas = list(_reservas_ativas_pedido(pedido))
    itens_controlados = list(pedido.itens.select_related('produto').filter(produto__controla_estoque=True))
    if len(reservas) != len(itens_controlados):
        raise ValidationError({'estoque': 'Reservas do pedido incompletas ou divergentes.'})
    for reserva in reservas:
        confirmar_reserva_estoque(reserva=reserva, usuario=operador, request=request)

    movimentacao = registrar_movimentacao_caixa_venda(venda=venda, operador=operador)
    _atribuir_numero_venda(venda=venda)
    venda.status = StatusOperacaoVenda.FINALIZADA
    venda.finalizada_em = timezone.now()
    venda.full_clean()
    venda.save(update_fields=['numero', 'status', 'finalizada_em', 'atualizada_em'])
    gerar_contas_receber_venda(venda=venda, usuario=operador, request=request)
    registrar_auditoria_finalizacao_venda(
        venda=venda, usuario=operador, movimentacao_caixa=movimentacao, request=request,
    )
    pedido.venda_pdv = venda
    pedido.status = StatusPedidoAtacado.FINALIZADO
    pedido.finalizado_em = venda.finalizada_em
    pedido.save(update_fields=['venda_pdv', 'status', 'finalizado_em'])
    return venda
