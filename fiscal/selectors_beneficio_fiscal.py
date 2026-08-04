from django.db.models import Q

from fiscal.models import BeneficioFiscal


def get_beneficios_fiscais(
    *,
    busca="",
    somente_ativos=False,
    uf="",
    tipo_beneficio="",
    regime_tributario="",
):
    registros = (
        BeneficioFiscal.objects.all()
        .order_by("codigo")
    )

    if somente_ativos:
        registros = registros.filter(ativo=True)

    uf = (uf or "").strip().upper()
    if uf:
        registros = registros.filter(uf=uf)

    tipo_beneficio = (tipo_beneficio or "").strip()
    if tipo_beneficio:
        registros = registros.filter(
            tipo_beneficio=tipo_beneficio,
        )

    regime_tributario = (
        regime_tributario or ""
    ).strip()
    if regime_tributario:
        registros = registros.filter(
            regime_tributario=regime_tributario,
        )

    busca = (busca or "").strip()
    if busca:
        registros = registros.filter(
            Q(codigo__icontains=busca)
            | Q(descricao__icontains=busca)
            | Q(fundamento_legal__icontains=busca)
            | Q(uf__icontains=busca)
        )

    return registros


def get_beneficio_fiscal(*, beneficio_id):
    return BeneficioFiscal.objects.get(id=beneficio_id)
