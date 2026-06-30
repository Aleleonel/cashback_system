from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria
from core.choices import StatusOperacional
from empresas.models import Loja
from core.models import ConfiguracaoSistema

def criar_loja_empresa(
    *,
    matriz,
    dados,
    usuario_executor,
    request=None
):

    loja = Loja.objects.create(
        matriz=matriz,
        nome=dados['nome'],
        cnpj=dados.get('cnpj') or None,
        telefone=dados.get('telefone') or None,
        status=dados['status']
    )

    registrar_auditoria(
        usuario=usuario_executor,
        matriz=matriz,
        loja=loja,
        acao=RegistroAuditoria.ACAO_CRIAR,
        recurso='empresa.loja',
        recurso_id=loja.id,
        descricao=f'Loja criada pela empresa: {loja.nome}',
        request=request
    )

    return loja


def editar_loja_empresa(
    *,
    loja,
    dados,
    usuario_executor,
    request=None
):

    loja.nome = dados['nome']
    loja.cnpj = dados.get('cnpj') or None
    loja.telefone = dados.get('telefone') or None
    loja.status = dados['status']

    loja.save(
        update_fields=[
            'nome',
            'cnpj',
            'telefone',
            'status',
            'atualizada_em',
        ]
    )

    registrar_auditoria(
        usuario=usuario_executor,
        matriz=loja.matriz,
        loja=loja,
        acao=RegistroAuditoria.ACAO_EDITAR,
        recurso='empresa.loja',
        recurso_id=loja.id,
        descricao=f'Loja editada pela empresa: {loja.nome}',
        request=request
    )

    return loja


def alternar_status_loja_empresa(
    *,
    loja,
    usuario_executor,
    request=None
):

    if loja.status == StatusOperacional.ATIVA:
        loja.status = StatusOperacional.SUSPENSA
        descricao_status = 'suspensa'
    else:
        loja.status = StatusOperacional.ATIVA
        descricao_status = 'ativada'

    loja.save(
        update_fields=[
            'status',
            'atualizada_em',
        ]
    )

    registrar_auditoria(
        usuario=usuario_executor,
        matriz=loja.matriz,
        loja=loja,
        acao=RegistroAuditoria.ACAO_EDITAR,
        recurso='empresa.loja',
        recurso_id=loja.id,
        descricao=f'Loja {descricao_status} pela empresa: {loja.nome}',
        request=request
    )

    return loja


def atualizar_configuracao_cashback_empresa(
    *,
    configuracao,
    dados,
    usuario_executor,
    request=None
):

    configuracao.percentual_cashback = dados['percentual_cashback']
    configuracao.dias_liberacao = dados['dias_liberacao']
    configuracao.dias_expiracao = dados['dias_expiracao']
    configuracao.valor_minimo_compra = dados['valor_minimo_compra']
    configuracao.enviar_email_saldo = dados['enviar_email_saldo']

    configuracao.save(
        update_fields=[
            'percentual_cashback',
            'dias_liberacao',
            'dias_expiracao',
            'valor_minimo_compra',
            'enviar_email_saldo',
            'atualizado_em',
        ]
    )

    registrar_auditoria(
        usuario=usuario_executor,
        matriz=configuracao.matriz,
        loja=None,
        acao=RegistroAuditoria.ACAO_EDITAR,
        recurso='empresa.configuracao_cashback',
        recurso_id=configuracao.id,
        descricao='Configuração de cashback atualizada pela empresa.',
        request=request
    )

    return configuracao