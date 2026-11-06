from decimal import Decimal
from datetime import datetime, time
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from .models import OrcamentoAtacado, ItemOrcamentoAtacado
from .pricing import ItemPrecificacao, precificar_atacado

@transaction.atomic
def criar_orcamento_atacado(*, matriz, loja, cliente, vendedor, itens, observacoes="", frete=Decimal("0.00"), validade=None, forma_pagamento=None, parcelas=1):
    if loja.matriz_id != matriz.pk or cliente.matriz_id != matriz.pk:
        raise ValidationError("Loja e cliente devem pertencer à matriz.")
    frete = Decimal(str(frete if frete is not None else "0"))
    if not frete.is_finite() or frete < 0 or frete.as_tuple().exponent < -2 or frete >= Decimal("1000000000000"):
        raise ValidationError("Frete invalido.")
    if validade is not None:
        if validade < timezone.localdate():
            raise ValidationError("A validade nao pode estar no passado.")
        validade = timezone.make_aware(datetime.combine(validade, time.max))
    if not isinstance(parcelas, int) or isinstance(parcelas, bool) or parcelas < 1:
        raise ValidationError("Quantidade de parcelas invalida.")
    if forma_pagamento is None:
        if parcelas != 1:
            raise ValidationError("Selecione uma forma de pagamento para parcelar.")
    else:
        from pdv.models import FormaPagamento
        forma = FormaPagamento.objects.filter(pk=forma_pagamento.pk, matriz=matriz, ativa=True, somente_funcionario=False).first()
        if forma is None:
            raise ValidationError("Forma de pagamento indisponivel para esta matriz.")
        limite = forma.maximo_parcelas if forma.permite_parcelamento else 1
        if parcelas > limite:
            raise ValidationError("Quantidade de parcelas acima do limite permitido.")
    entradas = list(itens)
    if not entradas:
        raise ValidationError("Inclua pelo menos um produto.")
    for produto, quantidade in entradas:
        if produto.matriz_id != matriz.pk:
            raise ValidationError("Produto de outra matriz.")
        if quantidade <= 0:
            raise ValidationError("Quantidade inválida.")
    resultado = precificar_atacado(matriz=matriz, itens=[
        ItemPrecificacao(produto=p, quantidade=q, preco_unitario=p.preco_venda)
        for p, q in entradas
    ])
    # A sequencia e protegida por lock da matriz; nao depende de numero global.
    type(matriz).objects.select_for_update().get(pk=matriz.pk)
    ultimo = OrcamentoAtacado.objects.filter(matriz=matriz).aggregate(n=Max("numero"))["n"] or 0
    orc = OrcamentoAtacado.objects.create(
        matriz=matriz, loja=loja, cliente=cliente, vendedor=vendedor,
        numero=ultimo + 1, observacoes=observacoes, frete=frete, valido_ate=validade,
        forma_pagamento=forma_pagamento, parcelas=parcelas,
    )
    for item in resultado.itens:
        percentual = resultado.percentual_desconto if item.atacado_elegivel and not item.produto_promocional else Decimal("0")
        ItemOrcamentoAtacado.objects.create(
            orcamento=orc, produto=item.produto, quantidade=item.quantidade,
            preco_unitario_original=item.preco_unitario_original,
            preco_unitario_base=item.preco_unitario_base,
            preco_unitario_final=item.preco_unitario_final,
            percentual_desconto_atacado=percentual,
            desconto_atacado=item.desconto_atacado,
            produto_promocional=item.produto_promocional,
            atacado_elegivel=item.atacado_elegivel,
            conta_para_enquadramento=item.conta_para_enquadramento,
        )
    orc.recalcular_totais()
    if orc.total != resultado.total_produtos + frete:
        raise ValidationError("Inconsistência entre os totais calculados e gravados.")
    return orc
