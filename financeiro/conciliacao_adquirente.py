"""Conciliação manual de repasses de cartão; reutiliza títulos e baixas existentes."""
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError
from django.db import transaction
from financeiro.models import PlanoConta, TituloFinanceiro, BaixaFinanceira
from financeiro.services import criar_lancamento_manual, registrar_baixa_financeira_com_caixa, estornar_baixa_financeira_com_caixa
from pdv.choices import TipoFormaPagamento
from pdv.models import PagamentoVenda


def _dinheiro(valor, campo, permitir_zero=False):
    try:
        numero = Decimal(str(valor))
        if not numero.is_finite() or numero.as_tuple().exponent < -2:
            raise ValueError()
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError({campo: 'Informe valor monetário válido com até duas casas decimais.'})
    if numero < 0 or (numero == 0 and not permitir_zero):
        raise ValidationError({campo: 'Valor fora do intervalo permitido.'})
    return numero.quantize(Decimal('0.01'))


@transaction.atomic
def registrar_repasse_adquirente(*, parcela, bruto, taxa, data, chave_idempotencia,
                                forma_pagamento, conta_financeira, plano_taxas=None,
                                usuario=None, request=None, observacao=''):
    """Baixa recebível bruto e paga despesa de taxa na mesma conta, com líquido no extrato."""
    if not chave_idempotencia or len(chave_idempotencia) > 95:
        raise ValidationError({'chave_idempotencia': 'Identificador inválido.'})
    if conta_financeira is None:
        raise ValidationError({'conta_financeira': 'Conta financeira obrigatória.'})
    bruto = _dinheiro(bruto, 'bruto')
    taxa = _dinheiro(taxa, 'taxa', permitir_zero=True)
    if taxa >= bruto:
        raise ValidationError({'taxa': 'Taxa deve ser inferior ao valor bruto.'})
    titulo = TituloFinanceiro.objects.select_for_update().get(pk=parcela.titulo_id)
    if titulo.natureza != TituloFinanceiro.Natureza.RECEBER or titulo.origem_tipo != TituloFinanceiro.OrigemTipo.VENDA_PAGAMENTO:
        raise ValidationError({'parcela': 'Repasse exige recebível originado de pagamento de venda.'})
    if forma_pagamento.matriz_id != titulo.matriz_id or not forma_pagamento.ativa:
        raise ValidationError({'forma_pagamento': 'Forma inativa ou pertencente a outra matriz.'})
    pagamento = PagamentoVenda.objects.select_related('venda', 'forma_pagamento').filter(
        uuid=titulo.origem_id, venda__matriz_id=titulo.matriz_id,
        venda__loja_id=titulo.loja_id,
    ).first()
    if pagamento is None or pagamento.forma_pagamento_id != forma_pagamento.pk:
        raise ValidationError({'parcela': 'Recebível não corresponde ao pagamento original em cartão.'})
    if titulo.chave_idempotencia != f'venda-pagamento:{pagamento.uuid}':
        raise ValidationError({'parcela': 'Identificação da origem financeira inconsistente.'})
    if forma_pagamento.tipo not in (TipoFormaPagamento.CARTAO_CREDITO, TipoFormaPagamento.CARTAO_DEBITO):
        raise ValidationError({'forma_pagamento': 'Repasse exige cartão de crédito ou débito.'})
    if taxa:
        if plano_taxas is None:
            raise ValidationError({'plano_taxas': 'Plano de despesa financeira obrigatório.'})
        if (plano_taxas.matriz_id != titulo.matriz_id or not plano_taxas.ativo
                or plano_taxas.tipo != PlanoConta.Tipo.ANALITICA or not plano_taxas.aceita_lancamento
                or plano_taxas.natureza != PlanoConta.Natureza.DESPESA
                or plano_taxas.classificacao_dre != PlanoConta.ClassificacaoDRE.RESULTADO_FINANCEIRO):
            raise ValidationError({'plano_taxas': 'Selecione conta analítica de despesa financeira da matriz.'})
    prefixo = f'adquirente:{chave_idempotencia}'
    baixa_anterior = BaixaFinanceira.objects.select_for_update().filter(
        parcela=parcela, chave_idempotencia=prefixo + ':bruto',
        tipo=BaixaFinanceira.Tipo.BAIXA,
    ).first()
    if baixa_anterior is not None:
        taxa_anterior = TituloFinanceiro.objects.filter(
            matriz=titulo.matriz, chave_idempotencia=prefixo + ':taxa',
        ).first()
        valor_taxa_anterior = taxa_anterior.valor_original if taxa_anterior else Decimal('0.00')
        if (baixa_anterior.valor != bruto or valor_taxa_anterior != taxa
                or baixa_anterior.data != data
                or baixa_anterior.forma_pagamento_id != forma_pagamento.pk
                or baixa_anterior.conta_financeira_id != conta_financeira.pk):
            raise ValidationError({'chave_idempotencia': 'Chave já utilizada com parâmetros diferentes.'})
    # Impede reutilizar uma conciliacao estornada ou gerar taxa duplicada
    # enquanto a despesa anterior continua economicamente ativa.
    if baixa_anterior is not None and BaixaFinanceira.objects.filter(
            baixa_estornada=baixa_anterior, tipo=BaixaFinanceira.Tipo.ESTORNO).exists():
        raise ValidationError({'parcela': 'Repasse ja estornado. Regularize o historico antes de conciliar novamente.'})
    taxas_anteriores = TituloFinanceiro.objects.filter(
        matriz=titulo.matriz,
        natureza=TituloFinanceiro.Natureza.PAGAR,
        origem_tipo=TituloFinanceiro.OrigemTipo.MANUAL,
        descricao=f'Taxa adquirente - recebível {titulo.pk}',
        chave_idempotencia__startswith='adquirente:',
        chave_idempotencia__endswith=':taxa',
    ).exclude(status=TituloFinanceiro.Status.CANCELADO)
    if taxas_anteriores.exclude(chave_idempotencia=prefixo + ':taxa').exists():
        raise ValidationError({'parcela': 'Existe taxa de adquirente ativa para este recebivel. Regularize-a antes de nova conciliacao.'})
    from financeiro._contexto_repasse import autorizar_registro_repasse
    with autorizar_registro_repasse():
        return _efetivar_repasse_adquirente(
            parcela=parcela, bruto=bruto, taxa=taxa, data=data,
            prefixo=prefixo, forma_pagamento=forma_pagamento,
            conta_financeira=conta_financeira, plano_taxas=plano_taxas,
            usuario=usuario, request=request, observacao=observacao,
            titulo=titulo,
        )


def _efetivar_repasse_adquirente(*, parcela, bruto, taxa, data, prefixo,
                                  forma_pagamento, conta_financeira, plano_taxas,
                                  usuario, request, observacao, titulo):
    baixa = registrar_baixa_financeira_com_caixa(
        parcela=parcela, valor=bruto, data=data, chave_idempotencia=prefixo + ':bruto',
        forma_pagamento=forma_pagamento, conta_financeira=conta_financeira,
        observacao=observacao, usuario=usuario, request=request)
    despesa = None
    if taxa:
        chave_despesa = prefixo + ':taxa'
        despesa = criar_lancamento_manual(
            matriz=titulo.matriz, loja=titulo.loja, natureza=TituloFinanceiro.Natureza.PAGAR,
            chave_idempotencia=chave_despesa, descricao=f'Taxa adquirente - recebível {titulo.pk}',
            data_emissao=data, data_competencia=data,
            parcelas=[{'numero': 1, 'vencimento': data, 'valor': taxa}],
            plano_conta=plano_taxas, valor_bruto=taxa, observacao=f'Repasse {prefixo}',
            usuario=usuario, request=request)
        registrar_baixa_financeira_com_caixa(
            parcela=despesa.parcelas.get(numero=1), valor=taxa, data=data,
            chave_idempotencia=prefixo + ':pagamento-taxa',
            forma_pagamento=forma_pagamento, conta_financeira=conta_financeira,
            observacao=f'Taxa descontada do repasse {prefixo}', usuario=usuario, request=request)
    return {'baixa': baixa, 'titulo_taxa': despesa, 'bruto': bruto,
            'taxa': taxa, 'liquido': bruto - taxa}


@transaction.atomic
def estornar_repasse_adquirente(*, baixa, data, chave_idempotencia, motivo, usuario=None, request=None):
    """Estorno integral do bruto e da taxa, em uma única transação."""
    from accounts.permissions import PERMISSAO_FINANCEIRO_GERENCIAR
    from accounts.services import usuario_tem_permissao
    from django.core.exceptions import PermissionDenied
    if usuario is None or not usuario_tem_permissao(usuario, PERMISSAO_FINANCEIRO_GERENCIAR):
        raise PermissionDenied('Estorno de repasse exige autorizacao financeira administrativa.')
    motivo = (motivo or '').strip()
    if len(motivo) < 11:
        raise ValidationError({'motivo': 'Informe justificativa com pelo menos 11 caracteres.'})
    original = BaixaFinanceira.objects.select_for_update().select_related('parcela__titulo').get(pk=baixa.pk)
    if original.tipo != BaixaFinanceira.Tipo.BAIXA or not original.chave_idempotencia.startswith('adquirente:') or not original.chave_idempotencia.endswith(':bruto'):
        raise ValidationError({'baixa': 'Não é um repasse conciliado.'})
    if not chave_idempotencia:
        raise ValidationError({'chave_idempotencia': 'Identificador obrigatório.'})
    prefixo = original.chave_idempotencia[:-6]
    titulo = original.parcela.titulo
    despesa = TituloFinanceiro.objects.filter(matriz=titulo.matriz, chave_idempotencia=prefixo + ':taxa').first()
    from financeiro._contexto_repasse import autorizar_estorno_repasse
    with autorizar_estorno_repasse():
        if despesa is not None:
            baixa_taxa = BaixaFinanceira.objects.get(parcela__titulo=despesa, chave_idempotencia=prefixo + ':pagamento-taxa', tipo=BaixaFinanceira.Tipo.BAIXA)
            estornar_baixa_financeira_com_caixa(
                baixa=baixa_taxa, valor=baixa_taxa.valor, data=data,
                chave_idempotencia=f'adquirente-estorno:{chave_idempotencia}:taxa',
                observacao=f'Estorno de repasse: {motivo}', usuario=usuario, request=request)
        estorno = estornar_baixa_financeira_com_caixa(
            baixa=original, valor=original.valor, data=data,
            chave_idempotencia=f'adquirente-estorno:{chave_idempotencia}:bruto',
            observacao=f'Estorno de repasse: {motivo}', usuario=usuario, request=request)
    return estorno
