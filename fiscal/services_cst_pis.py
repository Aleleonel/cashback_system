from django.core.exceptions import ValidationError
from django.db import transaction

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria
from fiscal.models import CSTPIS


def _validar(*, codigo, descricao, tipo_operacao, excluido=None):
    codigo = (codigo or "").strip()
    descricao = (descricao or "").strip()
    erros = {}

    if len(codigo) != 2 or not codigo.isdigit():
        erros["codigo"] = "Informe exatamente dois digitos."

    if not descricao:
        erros["descricao"] = "Informe a descricao do CST PIS."

    if tipo_operacao not in {
        CSTPIS.TIPO_ENTRADA,
        CSTPIS.TIPO_SAIDA,
        CSTPIS.TIPO_AMBOS,
    }:
        erros["tipo_operacao"] = "Informe um tipo de operacao valido."

    duplicados = CSTPIS.objects.filter(codigo=codigo)
    if excluido is not None:
        duplicados = duplicados.exclude(id=excluido.id)

    if codigo and duplicados.exists():
        erros["codigo"] = "Ja existe um CST PIS com este codigo."

    if erros:
        raise ValidationError(erros)

    return codigo, descricao


def _auditar(*, cst_pis, usuario, matriz, loja, request, acao, descricao):
    registrar_auditoria(
        usuario=usuario,
        matriz=matriz,
        loja=loja,
        acao=acao,
        recurso="fiscal.cst_pis",
        recurso_id=cst_pis.id,
        descricao=descricao,
        request=request,
    )


@transaction.atomic
def criar_cst_pis(*, dados, usuario_executor, matriz, loja=None, request=None):
    codigo, descricao = _validar(
        codigo=dados.get("codigo"),
        descricao=dados.get("descricao"),
        tipo_operacao=dados.get("tipo_operacao"),
    )

    cst_pis = CSTPIS(
        codigo=codigo,
        descricao=descricao,
        tipo_operacao=dados.get("tipo_operacao"),
        tributado=dados.get("tributado", False),
        exige_aliquota=dados.get("exige_aliquota", False),
        permite_credito=dados.get("permite_credito", False),
        exige_base_calculo=dados.get("exige_base_calculo", False),
        ativo=dados.get("ativo", True),
    )
    cst_pis.save()

    _auditar(
        cst_pis=cst_pis,
        usuario=usuario_executor,
        matriz=matriz,
        loja=loja,
        request=request,
        acao=RegistroAuditoria.ACAO_CRIAR,
        descricao=f"CST PIS criado: {cst_pis}",
    )

    return cst_pis


@transaction.atomic
def editar_cst_pis(*, cst_pis, dados, usuario_executor, matriz, loja=None, request=None):
    codigo, descricao = _validar(
        codigo=cst_pis.codigo,
        descricao=dados.get("descricao"),
        tipo_operacao=dados.get("tipo_operacao"),
        excluido=cst_pis,
    )

    cst_pis.codigo = codigo
    cst_pis.descricao = descricao
    cst_pis.tipo_operacao = dados.get("tipo_operacao")
    cst_pis.tributado = dados.get("tributado", cst_pis.tributado)
    cst_pis.exige_aliquota = dados.get("exige_aliquota", cst_pis.exige_aliquota)
    cst_pis.permite_credito = dados.get("permite_credito", cst_pis.permite_credito)
    cst_pis.exige_base_calculo = dados.get("exige_base_calculo", cst_pis.exige_base_calculo)
    cst_pis.ativo = dados.get("ativo", cst_pis.ativo)
    cst_pis.save()

    _auditar(
        cst_pis=cst_pis,
        usuario=usuario_executor,
        matriz=matriz,
        loja=loja,
        request=request,
        acao=RegistroAuditoria.ACAO_EDITAR,
        descricao=f"CST PIS atualizado: {cst_pis}",
    )

    return cst_pis
