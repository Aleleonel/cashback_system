from django.db import transaction

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria

from vouchers.models import Voucher, VoucherLoja
from .codigo import gerar_codigo_voucher


@transaction.atomic
def criar_voucher(*, matriz, dados, usuario_executor, request=None):

    voucher = Voucher.objects.create(
        matriz=matriz,
        cliente=dados.get('cliente'),
        codigo=gerar_codigo_voucher(),
        nome=dados['nome'],
        descricao=dados.get('descricao', ''),
        tipo=dados['tipo'],
        origem=Voucher.Origem.MANUAL,
        valor=dados.get('valor'),
        percentual=dados.get('percentual'),
        data_inicio=dados['data_inicio'],
        data_fim=dados['data_fim'],
        uso_unico_por_cliente=dados['uso_unico_por_cliente'],
        limite_utilizacao=dados['limite_utilizacao'],
    )

    lojas = dados.get('lojas')

    if lojas:
        VoucherLoja.objects.bulk_create([
            VoucherLoja(voucher=voucher, loja=loja)
            for loja in lojas
        ])

    registrar_auditoria(
        usuario=usuario_executor,
        matriz=matriz,
        loja=None,
        acao=RegistroAuditoria.ACAO_CRIAR,
        recurso='voucher',
        recurso_id=voucher.id,
        descricao=f'Voucher criado: {voucher.codigo}',
        request=request,
    )

    return voucher


@transaction.atomic
def editar_voucher(*, voucher, dados, usuario_executor, request=None):

    voucher.cliente = dados.get('cliente')
    voucher.nome = dados['nome']
    voucher.descricao = dados.get('descricao', '')
    voucher.tipo = dados['tipo']
    voucher.valor = dados.get('valor')
    voucher.percentual = dados.get('percentual')
    voucher.data_inicio = dados['data_inicio']
    voucher.data_fim = dados['data_fim']
    voucher.uso_unico_por_cliente = dados['uso_unico_por_cliente']
    voucher.limite_utilizacao = dados['limite_utilizacao']
    voucher.save()

    lojas = dados.get('lojas')

    voucher.lojas_permitidas.all().delete()

    if lojas:
        VoucherLoja.objects.bulk_create([
            VoucherLoja(voucher=voucher, loja=loja)
            for loja in lojas
        ])

    registrar_auditoria(
        usuario=usuario_executor,
        matriz=voucher.matriz,
        loja=None,
        acao=RegistroAuditoria.ACAO_EDITAR,
        recurso='voucher',
        recurso_id=voucher.id,
        descricao=f'Voucher alterado: {voucher.codigo}',
        request=request,
    )

    return voucher