from django.core.exceptions import ValidationError
from django.db import transaction

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria
from fiscal.models import RegraFiscal


def _auditar(
    *,
    regra,
    usuario,
    matriz,
    loja,
    request,
    acao,
    descricao,
):
    registrar_auditoria(
        usuario=usuario,
        matriz=matriz,
        loja=loja,
        acao=acao,
        recurso="fiscal.regra_fiscal",
        recurso_id=regra.id,
        descricao=descricao,
        request=request,
    )


def _aplicar_dados(regra, dados):
    campos = (
        "nome",
        "descricao",
        "prioridade",
        "ativo",
        "matriz",
        "loja",
        "regime_tributario",
        "tipo_operacao",
        "finalidade_operacao",
        "uf_origem",
        "uf_destino",
        "contribuinte_icms",
        "consumidor_final",
        "ncm",
        "cest",
        "cfop",
        "cst_icms",
        "csosn",
        "cst_pis",
        "cst_cofins",
        "cst_ipi",
        "beneficio_fiscal",
        "aliquota_icms",
        "reducao_base_icms",
        "aliquota_fcp",
        "aliquota_mva",
        "aliquota_pis",
        "aliquota_cofins",
        "aliquota_ipi",
        "diferimento_icms",
        "vigencia_inicio",
        "vigencia_fim",
    )

    for campo in campos:
        if campo in dados:
            setattr(regra, campo, dados.get(campo))

    return regra


@transaction.atomic
def criar_regra_fiscal(
    *,
    dados,
    usuario_executor,
    matriz_auditoria,
    loja_auditoria=None,
    request=None,
):
    codigo = RegraFiscal.normalizar_codigo(
        dados.get("codigo_interno")
    )

    if RegraFiscal.objects.filter(
        codigo_interno=codigo
    ).exists():
        raise ValidationError(
            {
                "codigo_interno": (
                    "Ja existe uma regra fiscal com este codigo."
                )
            }
        )

    regra = RegraFiscal(
        codigo_interno=codigo,
    )
    _aplicar_dados(regra, dados)
    regra.save()

    _auditar(
        regra=regra,
        usuario=usuario_executor,
        matriz=matriz_auditoria,
        loja=loja_auditoria,
        request=request,
        acao=RegistroAuditoria.ACAO_CRIAR,
        descricao=f"Regra fiscal criada: {regra}",
    )

    return regra


@transaction.atomic
def editar_regra_fiscal(
    *,
    regra,
    dados,
    usuario_executor,
    matriz_auditoria,
    loja_auditoria=None,
    request=None,
):
    codigo_original = regra.codigo_interno
    _aplicar_dados(regra, dados)
    regra.codigo_interno = codigo_original
    regra.save()

    _auditar(
        regra=regra,
        usuario=usuario_executor,
        matriz=matriz_auditoria,
        loja=loja_auditoria,
        request=request,
        acao=RegistroAuditoria.ACAO_EDITAR,
        descricao=f"Regra fiscal atualizada: {regra}",
    )

    return regra
