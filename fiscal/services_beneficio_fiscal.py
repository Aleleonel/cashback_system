from django.core.exceptions import ValidationError
from django.db import transaction

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria
from fiscal.models import BeneficioFiscal


def _validar(
    *,
    codigo,
    descricao,
    uf="",
    vigencia_inicio=None,
    vigencia_fim=None,
    excluido=None,
):
    codigo = BeneficioFiscal.normalizar_codigo(codigo)
    descricao = (descricao or "").strip()
    uf = BeneficioFiscal.normalizar_uf(uf)
    erros = {}

    if not codigo:
        erros["codigo"] = (
            "Informe o codigo do beneficio fiscal."
        )

    if not descricao:
        erros["descricao"] = (
            "Informe a descricao do beneficio fiscal."
        )

    if uf and len(uf) != 2:
        erros["uf"] = "Informe uma UF valida."

    if (
        vigencia_inicio
        and vigencia_fim
        and vigencia_fim < vigencia_inicio
    ):
        erros["vigencia_fim"] = (
            "O fim da vigencia nao pode ser anterior ao inicio."
        )

    duplicados = BeneficioFiscal.objects.filter(
        codigo=codigo
    )
    if excluido is not None:
        duplicados = duplicados.exclude(id=excluido.id)

    if codigo and duplicados.exists():
        erros["codigo"] = (
            "Ja existe um beneficio fiscal com este codigo."
        )

    if erros:
        raise ValidationError(erros)

    return codigo, descricao, uf


def _auditar(
    *,
    beneficio,
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
        recurso="fiscal.beneficio_fiscal",
        recurso_id=beneficio.id,
        descricao=descricao,
        request=request,
    )


@transaction.atomic
def criar_beneficio_fiscal(
    *,
    dados,
    usuario_executor,
    matriz,
    loja=None,
    request=None,
):
    codigo, descricao, uf = _validar(
        codigo=dados.get("codigo"),
        descricao=dados.get("descricao"),
        uf=dados.get("uf"),
        vigencia_inicio=dados.get("vigencia_inicio"),
        vigencia_fim=dados.get("vigencia_fim"),
    )

    beneficio = BeneficioFiscal(
        codigo=codigo,
        descricao=descricao,
        uf=uf,
        tipo_beneficio=dados.get("tipo_beneficio"),
        fundamento_legal=(
            dados.get("fundamento_legal") or ""
        ).strip(),
        percentual_reducao=dados.get(
            "percentual_reducao"
        ),
        percentual_credito=dados.get(
            "percentual_credito"
        ),
        exige_motivo_desoneracao=dados.get(
            "exige_motivo_desoneracao",
            False,
        ),
        motivo_desoneracao_padrao=(
            dados.get("motivo_desoneracao_padrao")
            or ""
        ).strip(),
        regime_tributario=dados.get(
            "regime_tributario",
            BeneficioFiscal.REGIME_TODOS,
        ),
        vigencia_inicio=dados.get("vigencia_inicio"),
        vigencia_fim=dados.get("vigencia_fim"),
        ativo=dados.get("ativo", True),
    )
    beneficio.save()

    _auditar(
        beneficio=beneficio,
        usuario=usuario_executor,
        matriz=matriz,
        loja=loja,
        request=request,
        acao=RegistroAuditoria.ACAO_CRIAR,
        descricao=(
            f"Beneficio fiscal criado: {beneficio}"
        ),
    )

    return beneficio


@transaction.atomic
def editar_beneficio_fiscal(
    *,
    beneficio,
    dados,
    usuario_executor,
    matriz,
    loja=None,
    request=None,
):
    codigo, descricao, uf = _validar(
        codigo=beneficio.codigo,
        descricao=dados.get("descricao"),
        uf=dados.get("uf"),
        vigencia_inicio=dados.get("vigencia_inicio"),
        vigencia_fim=dados.get("vigencia_fim"),
        excluido=beneficio,
    )

    beneficio.codigo = codigo
    beneficio.descricao = descricao
    beneficio.uf = uf
    beneficio.tipo_beneficio = dados.get(
        "tipo_beneficio"
    )
    beneficio.fundamento_legal = (
        dados.get("fundamento_legal") or ""
    ).strip()
    beneficio.percentual_reducao = dados.get(
        "percentual_reducao"
    )
    beneficio.percentual_credito = dados.get(
        "percentual_credito"
    )
    beneficio.exige_motivo_desoneracao = dados.get(
        "exige_motivo_desoneracao",
        False,
    )
    beneficio.motivo_desoneracao_padrao = (
        dados.get("motivo_desoneracao_padrao")
        or ""
    ).strip()
    beneficio.regime_tributario = dados.get(
        "regime_tributario",
        BeneficioFiscal.REGIME_TODOS,
    )
    beneficio.vigencia_inicio = dados.get(
        "vigencia_inicio"
    )
    beneficio.vigencia_fim = dados.get(
        "vigencia_fim"
    )
    beneficio.ativo = dados.get(
        "ativo",
        beneficio.ativo,
    )
    beneficio.save()

    _auditar(
        beneficio=beneficio,
        usuario=usuario_executor,
        matriz=matriz,
        loja=loja,
        request=request,
        acao=RegistroAuditoria.ACAO_EDITAR,
        descricao=(
            f"Beneficio fiscal atualizado: {beneficio}"
        ),
    )

    return beneficio
