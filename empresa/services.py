from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria
from core.choices import StatusOperacional
from empresas.models import Loja
from fiscal.models_emissao_fiscal import ConfiguracaoEmissaoFiscalLoja
from core.models import ConfiguracaoSistema
from accounts.models import PermissaoUsuario
from django.contrib.auth import get_user_model


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


def avaliar_prontidao_fiscal_loja(loja):
    """Avalia dados nao secretos necessarios para a filial emitir NFC-e."""
    from copy import copy
    from django.core.exceptions import ValidationError

    try:
        configuracao = loja.configuracao_emissao_fiscal
    except ConfiguracaoEmissaoFiscalLoja.DoesNotExist:
        return {"status":"incompleta","label":"Incompleta","detalhe":"Configuracao fiscal ainda nao cadastrada.","pendencias":("Configuracao fiscal de emissao nao cadastrada.",)}

    if not configuracao.ativa:
        return {"status":"inativa","label":"Inativa","detalhe":"Configuracao fiscal cadastrada, mas desativada.","pendencias":("Configuracao fiscal de emissao esta inativa.",)}

    pendencias = []
    cnpj = "".join(ch for ch in str(getattr(loja, "cnpj", "") or "") if ch.isdigit())
    if len(cnpj) != 14:
        pendencias.append("CNPJ da filial deve possuir 14 digitos.")

    configuracao_validacao = copy(configuracao)
    try:
        configuracao_validacao.full_clean()
    except ValidationError as exc:
        if hasattr(exc, "message_dict"):
            for campo, mensagens in exc.message_dict.items():
                for mensagem in mensagens:
                    pendencias.append(f"{campo}: {mensagem}")
        else:
            pendencias.extend(str(mensagem) for mensagem in exc.messages)

    try:
        serie = int(configuracao.serie_nfce)
    except (TypeError, ValueError):
        serie = 0
    if not 1 <= serie <= 999:
        pendencias.append("Serie NFC-e deve estar entre 1 e 999 para composicao da chave de acesso.")

    if pendencias:
        return {"status":"pendencias","label":"Com pendencias","detalhe":"Dados fiscais precisam ser corrigidos antes da emissao NFC-e.","pendencias":tuple(pendencias)}

    return {"status":"configurada","label":"Pronta","detalhe":"Dados fiscais nao secretos prontos para emissao NFC-e.","pendencias":()}

def salvar_configuracao_fiscal_loja_empresa(*, loja, dados, usuario_executor, request=None):
    try:
        configuracao = loja.configuracao_emissao_fiscal
        criada = False
    except ConfiguracaoEmissaoFiscalLoja.DoesNotExist:
        configuracao = ConfiguracaoEmissaoFiscalLoja(loja=loja)
        criada = True

    campos = [
        "razao_social", "nome_fantasia", "inscricao_estadual", "logradouro",
        "numero", "complemento", "bairro", "municipio", "codigo_municipio_ibge",
        "uf", "cep", "crt", "ambiente_nfce", "serie_nfce", "ativa",
    ]
    for campo in campos:
        setattr(configuracao, campo, dados[campo])

    configuracao.full_clean()
    configuracao.save()

    registrar_auditoria(
        usuario=usuario_executor,
        matriz=loja.matriz,
        loja=loja,
        acao=RegistroAuditoria.ACAO_CRIAR if criada else RegistroAuditoria.ACAO_EDITAR,
        recurso="empresa.loja.configuracao_fiscal",
        recurso_id=configuracao.id,
        descricao=("Configuracao fiscal da loja criada pela empresa." if criada else "Configuracao fiscal da loja atualizada pela empresa."),
        request=request,
    )
    return configuracao


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
    configuracao.percentual_maximo_beneficio = (
        dados['percentual_maximo_beneficio']
    )
    configuracao.dias_liberacao = dados['dias_liberacao']
    configuracao.dias_expiracao = dados['dias_expiracao']
    configuracao.valor_minimo_compra = dados['valor_minimo_compra']
    configuracao.enviar_email_saldo = dados['enviar_email_saldo']

    configuracao.save(
        update_fields=[
            'percentual_cashback',
            'percentual_maximo_beneficio',
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

def criar_usuario_empresa(
    *,
    matriz,
    dados,
    usuario_executor,
    request=None
):


    User = get_user_model()

    usuario = User.objects.create_user(
        username=dados['username'],
        email=dados.get('email') or '',
        password=dados['password'],
        first_name=dados.get('first_name') or '',
        telefone=dados.get('telefone') or None,
        perfil=dados['perfil'],
        matriz=matriz,
        ativo=dados.get('ativo', True),
    )

    usuario.lojas.set(dados['lojas'])

    sincronizar_permissoes_extras_usuario_empresa(
        usuario=usuario,
        permissoes=dados.get('permissoes_extras'),
        usuario_executor=usuario_executor,
        request=request
    )

    registrar_auditoria(
        usuario=usuario_executor,
        matriz=matriz,
        loja=None,
        acao=RegistroAuditoria.ACAO_CRIAR,
        recurso='empresa.usuario',
        recurso_id=usuario.id,
        descricao=f'Usuário criado pela empresa: {usuario.username}',
        request=request
    )

    return usuario


def editar_usuario_empresa(
    *,
    usuario,
    dados,
    usuario_executor,
    request=None
):

    usuario.username = dados['username']
    usuario.email = dados.get('email') or ''
    usuario.first_name = dados.get('first_name') or ''
    usuario.telefone = dados.get('telefone') or None
    usuario.perfil = dados['perfil']
    usuario.ativo = dados.get('ativo', False)

    senha = dados.get('password')

    if senha:
        usuario.set_password(senha)

    usuario.save(
        update_fields=[
            'username',
            'email',
            'first_name',
            'telefone',
            'perfil',
            'ativo',
            'password',
            'atualizado_em',
        ]
    )

    usuario.lojas.set(dados['lojas'])

    sincronizar_permissoes_extras_usuario_empresa(
        usuario=usuario,
        permissoes=dados.get('permissoes_extras'),
        usuario_executor=usuario_executor,
        request=request
    )

    registrar_auditoria(
        usuario=usuario_executor,
        matriz=usuario.matriz,
        loja=None,
        acao=RegistroAuditoria.ACAO_EDITAR,
        recurso='empresa.usuario',
        recurso_id=usuario.id,
        descricao=f'Usuário editado pela empresa: {usuario.username}',
        request=request
    )

    return usuario


def alternar_status_usuario_empresa(
    *,
    usuario,
    usuario_executor,
    request=None
):

    usuario.ativo = not usuario.ativo

    usuario.save(
        update_fields=[
            'ativo',
            'atualizado_em',
        ]
    )

    status = 'ativado' if usuario.ativo else 'inativado'

    registrar_auditoria(
        usuario=usuario_executor,
        matriz=usuario.matriz,
        loja=None,
        acao=RegistroAuditoria.ACAO_EDITAR,
        recurso='empresa.usuario',
        recurso_id=usuario.id,
        descricao=f'Usuário {status} pela empresa: {usuario.username}',
        request=request
    )

    return usuario


def sincronizar_permissoes_extras_usuario_empresa(
    *,
    usuario,
    permissoes,
    usuario_executor,
    request=None
):

    permissoes = set(permissoes or [])

    atuais = set(
        usuario.permissoes_extras.values_list(
            'permissao',
            flat=True
        )
    )

    adicionar = permissoes - atuais
    remover = atuais - permissoes

    for permissao in adicionar:
        PermissaoUsuario.objects.create(
            usuario=usuario,
            permissao=permissao
        )

    if remover:
        usuario.permissoes_extras.filter(
            permissao__in=remover
        ).delete()

    if adicionar or remover:
        registrar_auditoria(
            usuario=usuario_executor,
            matriz=usuario.matriz,
            loja=None,
            acao=RegistroAuditoria.ACAO_EDITAR,
            recurso='empresa.usuario.permissoes',
            recurso_id=usuario.id,
            descricao=(
                f'Permissões extras atualizadas para {usuario.username}. '
                f'Adicionadas: {", ".join(sorted(adicionar)) or "-"}. '
                f'Removidas: {", ".join(sorted(remover)) or "-"}.'
            ),
            request=request
        )