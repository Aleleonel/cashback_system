from django.db.models import Q

from .models import UsoVoucher, Voucher


def get_vouchers(
    *,
    matriz,
    busca='',
    status='',
    tipo='',
    origem='',
):

    vouchers = Voucher.objects.filter(
        matriz=matriz
    ).select_related(
        'cliente',
    ).prefetch_related(
        'lojas_permitidas__loja'
    ).order_by(
        '-criado_em'
    )

    if busca:
        vouchers = vouchers.filter(
            Q(codigo__icontains=busca) |
            Q(nome__icontains=busca) |
            Q(descricao__icontains=busca) |
            Q(cliente__nome__icontains=busca) |
            Q(cliente__cpf__icontains=busca)
        )

    if status:
        vouchers = vouchers.filter(
            status=status
        )

    if tipo:
        vouchers = vouchers.filter(
            tipo=tipo
        )

    if origem:
        vouchers = vouchers.filter(
            origem=origem
        )

    return vouchers


def get_voucher(
    *,
    matriz,
    voucher_id,
):

    return Voucher.objects.select_related(
        'cliente',
    ).prefetch_related(
        'lojas_permitidas__loja'
    ).get(
        matriz=matriz,
        id=voucher_id
    )


def get_vouchers_ativos(
    *,
    matriz,
):

    return Voucher.objects.filter(
        matriz=matriz,
        status=Voucher.Status.ATIVO
    ).order_by(
        'nome'
    )


def get_vouchers_cliente(
    *,
    matriz,
    cliente,
):

    return Voucher.objects.filter(
        matriz=matriz
    ).filter(
        Q(cliente__isnull=True) |
        Q(cliente=cliente)
    ).select_related(
        'cliente'
    ).order_by(
        'data_fim',
        'nome'
    )


def get_usos_voucher(
    *,
    matriz,
    voucher=None,
    cliente=None,
):

    usos = UsoVoucher.objects.filter(
        matriz=matriz
    ).select_related(
        'voucher',
        'cliente',
        'loja',
        'usuario',
    ).order_by(
        '-criado_em'
    )

    if voucher:
        usos = usos.filter(
            voucher=voucher
        )

    if cliente:
        usos = usos.filter(
            cliente=cliente
        )

    return usos

def get_relatorio_usos_voucher(
    *,
    matriz,
    loja=None,
    data_inicio=None,
    data_fim=None,
    voucher_id=None,
):
    usos = get_usos_voucher(matriz=matriz)
    if loja is not None:
        usos = usos.filter(loja=loja)
    if data_inicio is not None:
        usos = usos.filter(criado_em__date__gte=data_inicio)
    if data_fim is not None:
        usos = usos.filter(criado_em__date__lte=data_fim)
    if voucher_id:
        usos = usos.filter(voucher_id=voucher_id)
    return usos
