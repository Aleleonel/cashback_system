from django.db import transaction

from .models import ConfiguracaoComercial
from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria
from pdv.models import FormaPagamento


@transaction.atomic
def obter_ou_criar_configuracao_comercial(*, matriz):
    configuracao, _ = ConfiguracaoComercial.objects.get_or_create(matriz=matriz)
    return configuracao


@transaction.atomic
def atualizar_configuracao_comercial(*, configuracao, dados):
    campos_permitidos = {
        "atacado_ativo",
        "pedido_minimo_atacado",
        "desconto_atacado_percentual",
        "cashback_ativo",
        "voucher_ativo",
        "promocoes_ativas",
        "brindes_ativos",
        "arredondamento_ativo",
    }

    for campo, valor in dados.items():
        if campo in campos_permitidos:
            setattr(configuracao, campo, valor)

    configuracao.full_clean()
    configuracao.save()
    return configuracao


CAMPOS_FORMA_PAGAMENTO={"nome","codigo","tipo","ativa","permite_parcelamento","maximo_parcelas","exige_cliente_identificado","exige_autorizacao","gera_contas_receber","movimenta_caixa","permite_troco","somente_funcionario"}
@transaction.atomic
def criar_forma_pagamento(*,matriz,dados,usuario=None,request=None):
    forma=FormaPagamento(matriz=matriz)
    for campo,valor in dados.items():
        if campo in CAMPOS_FORMA_PAGAMENTO: setattr(forma,campo,valor)
    forma.full_clean();forma.save();registrar_auditoria(usuario=usuario,matriz=matriz,acao=RegistroAuditoria.ACAO_CRIAR,recurso="FormaPagamento",recurso_id=forma.pk,descricao=f"Forma de pagamento criada: {forma.nome} ({forma.codigo}).",request=request);return forma
@transaction.atomic
def atualizar_forma_pagamento(*,forma,dados,usuario=None,request=None):
    for campo,valor in dados.items():
        if campo in CAMPOS_FORMA_PAGAMENTO: setattr(forma,campo,valor)
    forma.full_clean();forma.save();registrar_auditoria(usuario=usuario,matriz=forma.matriz,acao=RegistroAuditoria.ACAO_EDITAR,recurso="FormaPagamento",recurso_id=forma.pk,descricao=f"Forma de pagamento atualizada: {forma.nome} ({forma.codigo}).",request=request);return forma
