from django.db.models import Q

from .models import (
    Fornecedor,
    PedidoCompra,
)


def get_fornecedores(
    *,
    matriz,
    busca='',
    status='',
):
    fornecedores = (
        Fornecedor.objects
        .filter(matriz=matriz)
        .select_related('matriz')
        .order_by(
            'razao_social',
            'id',
        )
    )

    busca = (busca or '').strip()
    status = (status or '').strip()

    if busca:
        busca_numerica = ''.join(
            caractere
            for caractere in busca
            if caractere.isdigit()
        )

        filtro = (
            Q(razao_social__icontains=busca)
            | Q(nome_fantasia__icontains=busca)
            | Q(email__icontains=busca)
            | Q(contato_principal__icontains=busca)
        )

        if busca_numerica:
            filtro |= Q(cnpj__icontains=busca_numerica)

        fornecedores = fornecedores.filter(filtro)

    if status:
        fornecedores = fornecedores.filter(status=status)

    return fornecedores


def get_fornecedor_por_uuid(
    *,
    matriz,
    fornecedor_uuid,
):
    return (
        Fornecedor.objects
        .select_related('matriz')
        .get(
            matriz=matriz,
            uuid=fornecedor_uuid,
        )
    )


def get_fornecedor_por_cnpj(
    *,
    matriz,
    cnpj,
):
    cnpj_normalizado = ''.join(
        caractere
        for caractere in (cnpj or '')
        if caractere.isdigit()
    )

    if not cnpj_normalizado:
        return None

    return (
        Fornecedor.objects
        .select_related('matriz')
        .filter(
            matriz=matriz,
            cnpj=cnpj_normalizado,
        )
        .first()
    )


def get_pedidos_compra(
    *,
    matriz,
    busca='',
    status='',
):
    pedidos = (
        PedidoCompra.objects
        .filter(matriz=matriz)
        .select_related(
            'fornecedor',
            'criado_por',
        )
        .prefetch_related(
            'itens',
        )
        .order_by(
            '-data_emissao',
            '-numero',
        )
    )

    busca = (busca or '').strip()
    status = (status or '').strip()

    if busca:
        filtro = (
            Q(fornecedor__razao_social__icontains=busca)
            | Q(fornecedor__nome_fantasia__icontains=busca)
            | Q(fornecedor__cnpj__icontains=busca)
        )

        if busca.isdigit():
            filtro |= Q(numero=int(busca))

        pedidos = pedidos.filter(filtro)

    if status:
        pedidos = pedidos.filter(status=status)

    return pedidos


def get_pedido_compra_por_uuid(
    *,
    matriz,
    pedido_uuid,
):
    return (
        PedidoCompra.objects
        .select_related(
            'matriz',
            'fornecedor',
            'criado_por',
        )
        .prefetch_related(
            'itens__produto',
        )
        .get(
            matriz=matriz,
            uuid=pedido_uuid,
        )
    )