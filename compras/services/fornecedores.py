from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria

from compras.choices import StatusFornecedor
from compras.models import Fornecedor


@transaction.atomic
def criar_fornecedor(
    *,
    matriz,
    dados,
    usuario=None,
    request=None,
):
    dados_normalizados = _normalizar_dados(dados)

    _validar_dados(
        matriz=matriz,
        dados=dados_normalizados,
    )

    try:
        fornecedor = Fornecedor.objects.create(
            matriz=matriz,
            **dados_normalizados,
        )
    except IntegrityError as erro:
        raise _traduzir_erro_integridade(
            matriz=matriz,
            dados=dados_normalizados,
            erro=erro,
        ) from erro

    registrar_auditoria(
        usuario=usuario,
        matriz=matriz,
        loja=None,
        acao=RegistroAuditoria.ACAO_CRIAR,
        recurso='compras.fornecedor',
        recurso_id=fornecedor.uuid,
        descricao=(
            f'Fornecedor criado: '
            f'razao_social={fornecedor.razao_social}; '
            f'cnpj={fornecedor.cnpj or "-"}.'
        ),
        request=request,
    )

    return fornecedor


@transaction.atomic
def editar_fornecedor(
    *,
    fornecedor,
    dados,
    usuario=None,
    request=None,
):
    fornecedor_bloqueado = (
        Fornecedor.objects
        .select_for_update()
        .select_related('matriz')
        .get(pk=fornecedor.pk)
    )

    dados_normalizados = _normalizar_dados(dados)

    _validar_dados(
        matriz=fornecedor_bloqueado.matriz,
        dados=dados_normalizados,
        fornecedor=fornecedor_bloqueado,
    )

    campos = [
        'razao_social',
        'nome_fantasia',
        'cnpj',
        'inscricao_estadual',
        'telefone',
        'whatsapp',
        'email',
        'contato_principal',
        'status',
        'observacoes',
    ]

    for campo in campos:
        setattr(
            fornecedor_bloqueado,
            campo,
            dados_normalizados[campo],
        )

    try:
        fornecedor_bloqueado.save(
            update_fields=[
                *campos,
                'atualizado_em',
            ]
        )
    except IntegrityError as erro:
        raise _traduzir_erro_integridade(
            matriz=fornecedor_bloqueado.matriz,
            dados=dados_normalizados,
            fornecedor=fornecedor_bloqueado,
            erro=erro,
        ) from erro

    registrar_auditoria(
        usuario=usuario,
        matriz=fornecedor_bloqueado.matriz,
        loja=None,
        acao=RegistroAuditoria.ACAO_EDITAR,
        recurso='compras.fornecedor',
        recurso_id=fornecedor_bloqueado.uuid,
        descricao=(
            f'Fornecedor editado: '
            f'razao_social={fornecedor_bloqueado.razao_social}; '
            f'cnpj={fornecedor_bloqueado.cnpj or "-"}.'
        ),
        request=request,
    )

    return fornecedor_bloqueado


@transaction.atomic
def alterar_status_fornecedor(
    *,
    fornecedor,
    status,
    usuario=None,
    request=None,
):
    fornecedor_bloqueado = (
        Fornecedor.objects
        .select_for_update()
        .select_related('matriz')
        .get(pk=fornecedor.pk)
    )

    if status not in StatusFornecedor.values:
        raise ValidationError({
            'status': 'Status de fornecedor invalido.'
        })

    if fornecedor_bloqueado.status == status:
        return fornecedor_bloqueado

    status_anterior = fornecedor_bloqueado.status
    fornecedor_bloqueado.status = status

    fornecedor_bloqueado.save(
        update_fields=[
            'status',
            'atualizado_em',
        ]
    )

    registrar_auditoria(
        usuario=usuario,
        matriz=fornecedor_bloqueado.matriz,
        loja=None,
        acao=RegistroAuditoria.ACAO_EDITAR,
        recurso='compras.fornecedor',
        recurso_id=fornecedor_bloqueado.uuid,
        descricao=(
            f'Status do fornecedor alterado: '
            f'razao_social={fornecedor_bloqueado.razao_social}; '
            f'anterior={status_anterior}; '
            f'novo={status}.'
        ),
        request=request,
    )

    return fornecedor_bloqueado


def _normalizar_dados(dados):
    dados = dados or {}

    return {
        'razao_social': _normalizar_texto(
            dados.get('razao_social')
        ),
        'nome_fantasia': _normalizar_texto(
            dados.get('nome_fantasia')
        ),
        'cnpj': _normalizar_documento(
            dados.get('cnpj')
        ),
        'inscricao_estadual': _normalizar_texto(
            dados.get('inscricao_estadual')
        ),
        'telefone': _normalizar_texto(
            dados.get('telefone')
        ),
        'whatsapp': _normalizar_texto(
            dados.get('whatsapp')
        ),
        'email': _normalizar_texto(
            dados.get('email')
        ).lower(),
        'contato_principal': _normalizar_texto(
            dados.get('contato_principal')
        ),
        'status': (
            dados.get('status')
            or StatusFornecedor.ATIVO
        ),
        'observacoes': _normalizar_texto(
            dados.get('observacoes')
        ),
    }


def _normalizar_texto(valor):
    return str(valor or '').strip()


def _normalizar_documento(valor):
    return ''.join(
        caractere
        for caractere in str(valor or '')
        if caractere.isdigit()
    )


def _validar_dados(
    *,
    matriz,
    dados,
    fornecedor=None,
):
    erros = {}

    if not matriz:
        erros['matriz'] = 'A matriz e obrigatoria.'

    if not dados['razao_social']:
        erros['razao_social'] = (
            'A razao social e obrigatoria.'
        )

    if dados['cnpj']:
        if len(dados['cnpj']) != 14:
            erros['cnpj'] = (
                'O CNPJ deve possuir 14 digitos.'
            )
        elif not _cnpj_valido(dados['cnpj']):
            erros['cnpj'] = (
                'O CNPJ informado e invalido.'
            )

    if dados['status'] not in StatusFornecedor.values:
        erros['status'] = (
            'Status de fornecedor invalido.'
        )

    if matriz and dados['razao_social']:
        duplicado_razao = Fornecedor.objects.filter(
            matriz=matriz,
            razao_social__iexact=dados['razao_social'],
        )

        if fornecedor is not None:
            duplicado_razao = duplicado_razao.exclude(
                pk=fornecedor.pk
            )

        if duplicado_razao.exists():
            erros['razao_social'] = (
                'Ja existe um fornecedor '
                'com esta razao social.'
            )

    if matriz and dados['cnpj']:
        duplicado_cnpj = Fornecedor.objects.filter(
            matriz=matriz,
            cnpj=dados['cnpj'],
        )

        if fornecedor is not None:
            duplicado_cnpj = duplicado_cnpj.exclude(
                pk=fornecedor.pk
            )

        if duplicado_cnpj.exists():
            erros['cnpj'] = (
                'Ja existe um fornecedor com este CNPJ.'
            )

    if erros:
        raise ValidationError(erros)


def _cnpj_valido(cnpj):
    if len(cnpj) != 14:
        return False

    if cnpj == cnpj[0] * 14:
        return False

    def calcular_digito(base, pesos):
        soma = sum(
            int(numero) * peso
            for numero, peso in zip(base, pesos)
        )
        resto = soma % 11

        return (
            '0'
            if resto < 2
            else str(11 - resto)
        )

    primeiro = calcular_digito(
        cnpj[:12],
        [
            5, 4, 3, 2,
            9, 8, 7, 6,
            5, 4, 3, 2,
        ],
    )

    segundo = calcular_digito(
        cnpj[:12] + primeiro,
        [
            6, 5, 4, 3, 2,
            9, 8, 7, 6,
            5, 4, 3, 2,
        ],
    )

    return cnpj[-2:] == primeiro + segundo


def _traduzir_erro_integridade(
    *,
    matriz,
    dados,
    erro,
    fornecedor=None,
):
    if dados.get('cnpj'):
        consulta = Fornecedor.objects.filter(
            matriz=matriz,
            cnpj=dados['cnpj'],
        )

        if fornecedor is not None:
            consulta = consulta.exclude(
                pk=fornecedor.pk
            )

        if consulta.exists():
            return ValidationError({
                'cnpj': (
                    'Ja existe um fornecedor '
                    'com este CNPJ.'
                )
            })

    consulta = Fornecedor.objects.filter(
        matriz=matriz,
        razao_social__iexact=dados['razao_social'],
    )

    if fornecedor is not None:
        consulta = consulta.exclude(
            pk=fornecedor.pk
        )

    if consulta.exists():
        return ValidationError({
            'razao_social': (
                'Ja existe um fornecedor '
                'com esta razao social.'
            )
        })

    return ValidationError({
        '__all__': (
            'Nao foi possivel salvar o fornecedor '
            'por conflito de integridade.'
        )
    })