from calendar import monthrange
from datetime import date

from django.core.paginator import Paginator
from django.db.models import Count, Sum

from vouchers.models import ComissaoParceiro


def consolidar_comissoes_parceiros(*, matriz, ano, mes):
    ano = int(ano)
    mes = int(mes)
    inicio = date(ano, mes, 1)
    fim = date(ano, mes, monthrange(ano, mes)[1])

    qs = (
        ComissaoParceiro.objects.filter(
            matriz=matriz,
            uso_voucher__criado_em__date__gte=inicio,
            uso_voucher__criado_em__date__lte=fim,
        )
        .values("parceiro_id", "parceiro__nome")
        .annotate(
            quantidade_vendas=Count("id"),
            total_vendas=Sum("uso_voucher__valor_compra"),
            total_descontos=Sum("uso_voucher__valor_desconto"),
            total_base=Sum("valor_base"),
            total_comissao=Sum("valor_comissao"),
        )
        .order_by("parceiro__nome", "parceiro_id")
    )

    return [
        {
            "parceiro_id": row["parceiro_id"],
            "parceiro_nome": row["parceiro__nome"],
            "quantidade_vendas": row["quantidade_vendas"],
            "total_vendas": row["total_vendas"],
            "total_descontos": row["total_descontos"],
            "total_base": row["total_base"],
            "total_comissao": row["total_comissao"],
            "ano": ano,
            "mes": mes,
        }
        for row in qs
    ]

def listar_detalhes_comissoes_parceiro(
    *, matriz, parceiro_id, ano, mes, pagina=1, por_pagina=20
):
    ano = int(ano)
    mes = int(mes)
    pagina = int(pagina)
    por_pagina = int(por_pagina)

    if por_pagina < 1:
        por_pagina = 20
    por_pagina = min(por_pagina, 100)

    inicio = date(ano, mes, 1)
    fim = date(ano, mes, monthrange(ano, mes)[1])

    qs = (
        ComissaoParceiro.objects.filter(
            matriz=matriz,
            parceiro_id=parceiro_id,
            uso_voucher__criado_em__date__gte=inicio,
            uso_voucher__criado_em__date__lte=fim,
        )
        .select_related(
            "parceiro",
            "uso_voucher",
            "uso_voucher__voucher",
            "uso_voucher__loja",
        )
        .order_by("-uso_voucher__criado_em", "-pk")
    )

    return Paginator(qs, por_pagina).get_page(pagina)
