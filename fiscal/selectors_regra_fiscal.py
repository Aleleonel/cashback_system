from django.db.models import Q

from fiscal.models import RegraFiscal


def get_regras_fiscais(
    *,
    busca="",
    somente_ativas=False,
    regime_tributario="",
    tipo_operacao="",
    finalidade_operacao="",
    uf_origem="",
    uf_destino="",
):
    regras = (
        RegraFiscal.objects.select_related(
            "matriz",
            "loja",
            "ncm",
            "cest",
            "cfop",
            "cst_icms",
            "csosn",
            "cst_pis",
            "cst_cofins",
            "cst_ipi",
            "beneficio_fiscal",
        )
        .order_by("prioridade", "codigo_interno")
    )

    if somente_ativas:
        regras = regras.filter(ativo=True)
    if regime_tributario:
        regras = regras.filter(regime_tributario=regime_tributario)
    if tipo_operacao:
        regras = regras.filter(tipo_operacao=tipo_operacao)
    if finalidade_operacao:
        regras = regras.filter(finalidade_operacao=finalidade_operacao)
    if uf_origem:
        regras = regras.filter(uf_origem=uf_origem.strip().upper())
    if uf_destino:
        regras = regras.filter(uf_destino=uf_destino.strip().upper())

    busca = (busca or "").strip()
    if busca:
        regras = regras.filter(
            Q(codigo_interno__icontains=busca)
            | Q(nome__icontains=busca)
            | Q(descricao__icontains=busca)
        )

    return regras


def get_regra_fiscal(*, regra_id):
    return RegraFiscal.objects.get(id=regra_id)


def get_regras_ativas_vigentes(*, data_operacao):
    return get_regras_fiscais(somente_ativas=True).filter(
        Q(vigencia_inicio__isnull=True)
        | Q(vigencia_inicio__lte=data_operacao),
        Q(vigencia_fim__isnull=True)
        | Q(vigencia_fim__gte=data_operacao),
    )
