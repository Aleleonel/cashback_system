from django.core.exceptions import ValidationError
from django.db import transaction

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria
from fiscal.models import CSTIPI


def _validar(*, codigo, descricao, tipo_operacao, excluido=None):
    codigo = (codigo or "").strip()
    descricao = (descricao or "").strip()
    erros = {}

    if len(codigo) != 2 or not codigo.isdigit():
        erros["codigo"] = "Informe exatamente dois digitos."

    if not descricao:
        erros["descricao"] = "Informe a descricao do CST IPI."

    if tipo_operacao not in {
        CSTIPI.TIPO_ENTRADA,
        CSTIPI.TIPO_SAIDA,
        CSTIPI.TIPO_AMBOS,
    }:
        erros["tipo_operacao"] = "Informe um tipo de operacao valido."

    duplicados = CSTIPI.objects.filter(codigo=codigo)
    if excluido is not None:
        duplicados = duplicados.exclude(id=excluido.id)

    if codigo and duplicados.exists():
        erros["codigo"] = "Ja existe um CST IPI com este codigo."

    if erros:
        raise ValidationError(erros)

    return codigo, descricao


def _auditar(*, cst_ipi, usuario, matriz, loja, request, acao, descricao):
    registrar_auditoria(
        usuario=usuario,
        matriz=matriz,
        loja=loja,
        acao=acao,
        recurso="fiscal.cst_ipi",
        recurso_id=cst_ipi.id,
        descricao=descricao,
        request=request,
    )


@transaction.atomic
def criar_cst_ipi(*, dados, usuario_executor, matriz, loja=None, request=None):
    codigo, descricao = _validar(
        codigo=dados.get("codigo"),
        descricao=dados.get("descricao"),
        tipo_operacao=dados.get("tipo_operacao"),
    )

    cst_ipi = CSTIPI(
        codigo=codigo,
        descricao=descricao,
        tipo_operacao=dados.get("tipo_operacao"),
        tributado=dados.get("tributado", False),
        exige_aliquota=dados.get("exige_aliquota", False),
        permite_credito=dados.get("permite_credito", False),
        exige_base_calculo=dados.get("exige_base_calculo", False),
        exige_codigo_enquadramento=dados.get(
            "exige_codigo_enquadramento",
            False,
        ),
        ativo=dados.get("ativo", True),
    )
    cst_ipi.save()

    _auditar(
        cst_ipi=cst_ipi,
        usuario=usuario_executor,
        matriz=matriz,
        loja=loja,
        request=request,
        acao=RegistroAuditoria.ACAO_CRIAR,
        descricao=f"CST IPI criado: {cst_ipi}",
    )

    return cst_ipi


@transaction.atomic
def editar_cst_ipi(*, cst_ipi, dados, usuario_executor, matriz, loja=None, request=None):
    codigo, descricao = _validar(
        codigo=cst_ipi.codigo,
        descricao=dados.get("descricao"),
        tipo_operacao=dados.get("tipo_operacao"),
        excluido=cst_ipi,
    )

    cst_ipi.codigo = codigo
    cst_ipi.descricao = descricao
    cst_ipi.tipo_operacao = dados.get("tipo_operacao")
    cst_ipi.tributado = dados.get("tributado", cst_ipi.tributado)
    cst_ipi.exige_aliquota = dados.get("exige_aliquota", cst_ipi.exige_aliquota)
    cst_ipi.permite_credito = dados.get("permite_credito", cst_ipi.permite_credito)
    cst_ipi.exige_base_calculo = dados.get("exige_base_calculo", cst_ipi.exige_base_calculo)
    cst_ipi.exige_codigo_enquadramento = dados.get(
        "exige_codigo_enquadramento",
        cst_ipi.exige_codigo_enquadramento,
    )
    cst_ipi.ativo = dados.get("ativo", cst_ipi.ativo)
    cst_ipi.save()

    _auditar(
        cst_ipi=cst_ipi,
        usuario=usuario_executor,
        matriz=matriz,
        loja=loja,
        request=request,
        acao=RegistroAuditoria.ACAO_EDITAR,
        descricao=f"CST IPI atualizado: {cst_ipi}",
    )

    return cst_ipi
