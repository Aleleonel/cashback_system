from django.core.exceptions import ValidationError
from django.db import transaction

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria
from fiscal.models import OrigemMercadoria


def _normalizar_codigo(codigo):
    return (codigo or "").strip()


def _normalizar_descricao(descricao):
    return (descricao or "").strip()


def _validar_dados(
    *,
    codigo,
    descricao,
    origem_excluida=None,
):
    codigo = _normalizar_codigo(codigo)
    descricao = _normalizar_descricao(descricao)
    erros = {}

    if (
        len(codigo) != 1
        or not codigo.isdigit()
        or codigo not in "012345678"
    ):
        erros["codigo"] = "Informe um codigo entre 0 e 8."

    if not descricao:
        erros["descricao"] = "Informe a descricao da origem."

    duplicadas = OrigemMercadoria.objects.filter(
        codigo=codigo,
    )

    if origem_excluida is not None:
        duplicadas = duplicadas.exclude(
            id=origem_excluida.id,
        )

    if codigo and duplicadas.exists():
        erros["codigo"] = (
            "Ja existe uma origem com este codigo."
        )

    if erros:
        raise ValidationError(erros)

    return codigo, descricao


def _auditar(
    *,
    origem,
    usuario_executor,
    matriz,
    loja,
    request,
    acao,
    descricao,
):
    registrar_auditoria(
        usuario=usuario_executor,
        matriz=matriz,
        loja=loja,
        acao=acao,
        recurso="fiscal.origem_mercadoria",
        recurso_id=origem.id,
        descricao=descricao,
        request=request,
    )


@transaction.atomic
def criar_origem_mercadoria(
    *,
    dados,
    usuario_executor,
    matriz,
    loja=None,
    request=None,
):
    codigo, descricao = _validar_dados(
        codigo=dados.get("codigo"),
        descricao=dados.get("descricao"),
    )

    origem = OrigemMercadoria(
        codigo=codigo,
        descricao=descricao,
        ativo=dados.get("ativo", True),
    )
    origem.full_clean()
    origem.save()

    _auditar(
        origem=origem,
        usuario_executor=usuario_executor,
        matriz=matriz,
        loja=loja,
        request=request,
        acao=RegistroAuditoria.ACAO_CRIAR,
        descricao=f"Origem da mercadoria criada: {origem}",
    )

    return origem


@transaction.atomic
def editar_origem_mercadoria(
    *,
    origem,
    dados,
    usuario_executor,
    matriz,
    loja=None,
    request=None,
):
    codigo, descricao = _validar_dados(
        codigo=origem.codigo,
        descricao=dados.get("descricao"),
        origem_excluida=origem,
    )

    origem.codigo = codigo
    origem.descricao = descricao
    origem.ativo = dados.get(
        "ativo",
        origem.ativo,
    )
    origem.full_clean()
    origem.save(
        update_fields=(
            "codigo",
            "descricao",
            "ativo",
            "atualizado_em",
        )
    )

    _auditar(
        origem=origem,
        usuario_executor=usuario_executor,
        matriz=matriz,
        loja=loja,
        request=request,
        acao=RegistroAuditoria.ACAO_EDITAR,
        descricao=f"Origem da mercadoria atualizada: {origem}",
    )

    return origem

from fiscal.services_cst_icms import (
    criar_cst_icms,
    editar_cst_icms,
)

from fiscal.services_csosn import (
    criar_csosn,
    editar_csosn,
)

from fiscal.services_cfop import (
    criar_cfop,
    editar_cfop,
)

from fiscal.services_ncm import (
    criar_ncm,
    editar_ncm,
)

from fiscal.services_cst_pis import (
    criar_cst_pis,
    editar_cst_pis,
)

from fiscal.services_cst_cofins import (
    criar_cst_cofins,
    editar_cst_cofins,
)

from fiscal.services_cst_ipi import (
    criar_cst_ipi,
    editar_cst_ipi,
)

from fiscal.services_cest import (
    criar_cest,
    editar_cest,
)

from fiscal.services_beneficio_fiscal import (
    criar_beneficio_fiscal,
    editar_beneficio_fiscal,
)

from fiscal.services_regra_fiscal import (
    criar_regra_fiscal,
    editar_regra_fiscal,
)

from fiscal.services_motor_selecao import (
    RegraFiscalAmbiguaError,
    selecionar_regra,
    selecionar_regra_fiscal,
)

from fiscal.services_motor_tributario import (
    calcular_tributos,
    quantizar_intermediario,
    quantizar_moeda,
)
