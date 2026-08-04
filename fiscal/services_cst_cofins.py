from django.core.exceptions import ValidationError
from django.db import transaction

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria
from fiscal.models import CSTCOFINS


def _validar(*, codigo, descricao, tipo_operacao, excluido=None):
    codigo = (codigo or "").strip()
    descricao = (descricao or "").strip()
    erros = {}

    if len(codigo) != 2 or not codigo.isdigit():
        erros["codigo"] = "Informe exatamente dois digitos."

    if not descricao:
        erros["descricao"] = "Informe a descricao do CST COFINS."

    if tipo_operacao not in {
        CSTCOFINS.TIPO_ENTRADA,
        CSTCOFINS.TIPO_SAIDA,
        CSTCOFINS.TIPO_AMBOS,
    }:
        erros["tipo_operacao"] = "Informe um tipo de operacao valido."

    duplicados = CSTCOFINS.objects.filter(codigo=codigo)
    if excluido is not None:
        duplicados = duplicados.exclude(id=excluido.id)

    if codigo and duplicados.exists():
        erros["codigo"] = "Ja existe um CST COFINS com este codigo."

    if erros:
        raise ValidationError(erros)

    return codigo, descricao


def _auditar(*, cst_cofins, usuario, matriz, loja, request, acao, descricao):
    registrar_auditoria(
        usuario=usuario,
        matriz=matriz,
        loja=loja,
        acao=acao,
        recurso="fiscal.cst_cofins",
        recurso_id=cst_cofins.id,
        descricao=descricao,
        request=request,
    )


@transaction.atomic
def criar_cst_cofins(*, dados, usuario_executor, matriz, loja=None, request=None):
    codigo, descricao = _validar(
        codigo=dados.get("codigo"),
        descricao=dados.get("descricao"),
        tipo_operacao=dados.get("tipo_operacao"),
    )

    cst_cofins = CSTCOFINS(
        codigo=codigo,
        descricao=descricao,
        tipo_operacao=dados.get("tipo_operacao"),
        tributado=dados.get("tributado", False),
        exige_aliquota=dados.get("exige_aliquota", False),
        permite_credito=dados.get("permite_credito", False),
        exige_base_calculo=dados.get("exige_base_calculo", False),
        ativo=dados.get("ativo", True),
    )
    cst_cofins.save()

    _auditar(
        cst_cofins=cst_cofins,
        usuario=usuario_executor,
        matriz=matriz,
        loja=loja,
        request=request,
        acao=RegistroAuditoria.ACAO_CRIAR,
        descricao=f"CST COFINS criado: {cst_cofins}",
    )

    return cst_cofins


@transaction.atomic
def editar_cst_cofins(*, cst_cofins, dados, usuario_executor, matriz, loja=None, request=None):
    codigo, descricao = _validar(
        codigo=cst_cofins.codigo,
        descricao=dados.get("descricao"),
        tipo_operacao=dados.get("tipo_operacao"),
        excluido=cst_cofins,
    )

    cst_cofins.codigo = codigo
    cst_cofins.descricao = descricao
    cst_cofins.tipo_operacao = dados.get("tipo_operacao")
    cst_cofins.tributado = dados.get("tributado", cst_cofins.tributado)
    cst_cofins.exige_aliquota = dados.get("exige_aliquota", cst_cofins.exige_aliquota)
    cst_cofins.permite_credito = dados.get("permite_credito", cst_cofins.permite_credito)
    cst_cofins.exige_base_calculo = dados.get("exige_base_calculo", cst_cofins.exige_base_calculo)
    cst_cofins.ativo = dados.get("ativo", cst_cofins.ativo)
    cst_cofins.save()

    _auditar(
        cst_cofins=cst_cofins,
        usuario=usuario_executor,
        matriz=matriz,
        loja=loja,
        request=request,
        acao=RegistroAuditoria.ACAO_EDITAR,
        descricao=f"CST COFINS atualizado: {cst_cofins}",
    )

    return cst_cofins
