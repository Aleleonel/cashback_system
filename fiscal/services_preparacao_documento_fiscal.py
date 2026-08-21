from hashlib import sha256

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from fiscal.choices_documento_fiscal import (
    AmbienteDocumentoFiscal,
    ModeloDocumentoFiscal,
    StatusDocumentoFiscal,
)
from fiscal.dto_documento_fiscal import (
    DadosDestinatarioDocumentoFiscal,
    DadosDocumentoFiscal,
    DadosEmitenteDocumentoFiscal,
    DadosItemDocumentoFiscal,
    DadosPagamentoDocumentoFiscal,
)
from fiscal.models_documento_fiscal import DocumentoFiscal
from fiscal.services_documento_fiscal import (
    reservar_proximo_numero_documento_fiscal,
    transicionar_documento_fiscal,
)


def _texto(valor):
    return str(valor or "").strip()


def gerar_idempotency_key_documento_fiscal(
    *,
    venda_fiscal_id,
    modelo,
    ambiente,
    serie,
):
    origem = (
        f"v1|venda_fiscal={int(venda_fiscal_id)}"
        f"|modelo={modelo}"
        f"|ambiente={ambiente}"
        f"|serie={int(serie)}"
    )

    digest = sha256(
        origem.encode("utf-8")
    ).hexdigest()

    return f"docfiscal:v1:{digest}"


def _validar_parametros_preparacao(
    *,
    venda_fiscal,
    modelo,
    ambiente,
    serie,
):
    errors = {}

    if not getattr(venda_fiscal, "pk", None):
        errors["venda_fiscal"] = (
            "VendaFiscal precisa estar persistida."
        )

    if modelo not in ModeloDocumentoFiscal.values:
        errors["modelo"] = "Modelo fiscal invalido."

    if ambiente not in AmbienteDocumentoFiscal.values:
        errors["ambiente"] = "Ambiente fiscal invalido."

    if not isinstance(serie, int) or serie < 1:
        errors["serie"] = "A serie deve ser maior que zero."

    venda = getattr(venda_fiscal, "venda", None)

    if venda is None:
        errors["venda_fiscal"] = (
            "VendaFiscal precisa possuir venda relacionada."
        )
    else:
        if not getattr(venda, "matriz_id", None):
            errors["matriz"] = "Venda fiscal sem matriz."

        if not getattr(venda, "loja_id", None):
            errors["loja"] = "Venda fiscal sem loja."

    if errors:
        raise ValidationError(errors)


def _codigo_unidade_comercial(produto):
    unidade = getattr(produto, "unidade_medida", None)
    for atributo in ("sigla", "codigo", "abreviacao", "nome"):
        valor = _texto(getattr(unidade, atributo, ""))
        if valor:
            return valor
    return ""


def _item_snapshot_para_dto(item_fiscal):
    item_venda = item_fiscal.item_venda
    produto = item_venda.produto

    return DadosItemDocumentoFiscal(
        item_venda_id=item_fiscal.item_venda_id,
        origem_mercadoria_codigo=_texto(
            item_fiscal.origem_mercadoria_codigo
        ),
        ncm_codigo=_texto(item_fiscal.ncm_codigo),
        ncm_descricao=_texto(item_fiscal.ncm_descricao),
        cest_codigo=_texto(item_fiscal.cest_codigo),
        cfop_codigo=_texto(item_fiscal.cfop_codigo),
        cfop_descricao=_texto(item_fiscal.cfop_descricao),
        cst_icms_codigo=_texto(item_fiscal.cst_icms_codigo),
        csosn_codigo=_texto(item_fiscal.csosn_codigo),
        cst_pis_codigo=_texto(item_fiscal.cst_pis_codigo),
        cst_cofins_codigo=_texto(
            item_fiscal.cst_cofins_codigo
        ),
        cst_ipi_codigo=_texto(item_fiscal.cst_ipi_codigo),
        regime_tributario=_texto(
            item_fiscal.regime_tributario
        ),
        uf_origem=_texto(item_fiscal.uf_origem),
        uf_destino=_texto(item_fiscal.uf_destino),
        tipo_operacao=_texto(item_fiscal.tipo_operacao),
        finalidade_operacao=_texto(
            item_fiscal.finalidade_operacao
        ),
        contribuinte_icms=bool(item_fiscal.contribuinte_icms),
        consumidor_final=bool(item_fiscal.consumidor_final),
        quantidade=item_fiscal.quantidade,
        valor_unitario=item_fiscal.valor_unitario,
        valor_produtos=item_fiscal.valor_produtos,
        desconto=item_fiscal.desconto,
        acrescimo=item_fiscal.acrescimo,
        frete=item_fiscal.frete,
        seguro=item_fiscal.seguro,
        outras_despesas=item_fiscal.outras_despesas,
        base_operacao=item_fiscal.base_operacao,
        base_icms=item_fiscal.base_icms,
        aliquota_icms=item_fiscal.aliquota_icms,
        valor_icms=item_fiscal.valor_icms,
        base_fcp=item_fiscal.base_fcp,
        aliquota_fcp=item_fiscal.aliquota_fcp,
        valor_fcp=item_fiscal.valor_fcp,
        base_pis=item_fiscal.base_pis,
        aliquota_pis=item_fiscal.aliquota_pis,
        valor_pis=item_fiscal.valor_pis,
        base_cofins=item_fiscal.base_cofins,
        aliquota_cofins=item_fiscal.aliquota_cofins,
        valor_cofins=item_fiscal.valor_cofins,
        base_ipi=item_fiscal.base_ipi,
        aliquota_ipi=item_fiscal.aliquota_ipi,
        valor_ipi=item_fiscal.valor_ipi,
        valor_total_tributos=item_fiscal.valor_total_tributos,
        codigo_produto=(
            _texto(getattr(produto, "codigo_interno", ""))
            or _texto(getattr(produto, "sku", ""))
            or str(produto.pk)
        ),
        descricao_produto=(
            _texto(getattr(produto, "nome", ""))
            or _texto(getattr(produto, "descricao", ""))
        ),
        unidade_comercial=_codigo_unidade_comercial(produto),
        gtin=_texto(getattr(produto, "gtin", "")),
    )



def _construir_emitente_documento_fiscal(venda):
    try:
        configuracao = venda.loja.configuracao_emissao_fiscal
    except Exception:
        return None

    if not configuracao.ativa:
        return None

    return DadosEmitenteDocumentoFiscal(
        cnpj=_texto(getattr(venda.loja, "cnpj", "")),
        razao_social=_texto(configuracao.razao_social),
        nome_fantasia=_texto(configuracao.nome_fantasia),
        inscricao_estadual=_texto(configuracao.inscricao_estadual),
        crt=_texto(configuracao.crt),
        logradouro=_texto(configuracao.logradouro),
        numero=_texto(configuracao.numero),
        complemento=_texto(configuracao.complemento),
        bairro=_texto(configuracao.bairro),
        codigo_municipio_ibge=_texto(configuracao.codigo_municipio_ibge),
        municipio=_texto(configuracao.municipio),
        uf=_texto(configuracao.uf),
        cep=_texto(configuracao.cep),
    )


def _construir_destinatario_documento_fiscal(venda):
    cliente = getattr(venda, "cliente", None)
    if cliente is None:
        return None

    cpf = _texto(getattr(cliente, "cpf_normalizado", ""))
    if not cpf:
        cpf = "".join(ch for ch in _texto(getattr(cliente, "cpf", "")) if ch.isdigit())

    if not cpf or cpf.upper() == "CONSUMIDOR":
        return None

    return DadosDestinatarioDocumentoFiscal(
        cpf_cnpj=cpf,
        nome=_texto(getattr(cliente, "nome", "")),
        email=_texto(getattr(cliente, "email", "")),
    )


def _construir_pagamentos_documento_fiscal(venda):
    pagamentos = []
    for pagamento in (
        venda.pagamentos.select_related("forma_pagamento").order_by("criado_em", "id")
    ):
        forma = pagamento.forma_pagamento
        pagamentos.append(
            DadosPagamentoDocumentoFiscal(
                codigo=_texto(getattr(forma, "codigo", "")),
                tipo=_texto(getattr(forma, "tipo", "")),
                descricao=_texto(getattr(forma, "nome", "")),
                valor=pagamento.valor,
                troco=pagamento.troco,
            )
        )
    return tuple(pagamentos)

def construir_dados_documento_fiscal(
    *,
    venda_fiscal,
    modelo,
    ambiente,
    serie,
    numero=None,
):
    venda = venda_fiscal.venda

    itens = []

    for item_venda in (
        venda.itens
        .filter(cancelado=False)
        .select_related(
            "fiscal",
            "produto",
            "produto__unidade_medida",
        )
        .order_by("id")
    ):
        try:
            item_fiscal = item_venda.fiscal
        except Exception as exc:
            raise ValidationError({
                "itens": (
                    "Todos os itens ativos precisam possuir "
                    "ItemVendaFiscal."
                )
            }) from exc

        itens.append(
            _item_snapshot_para_dto(item_fiscal)
        )

    return DadosDocumentoFiscal(
        venda_fiscal_id=venda_fiscal.pk,
        venda_id=venda.pk,
        matriz_id=venda.matriz_id,
        loja_id=venda.loja_id,
        modelo=modelo,
        ambiente=ambiente,
        serie=serie,
        numero=numero,
        regime_tributario=_texto(
            venda_fiscal.regime_tributario
        ),
        uf_origem=_texto(venda_fiscal.uf_origem),
        uf_destino=_texto(venda_fiscal.uf_destino),
        tipo_operacao=_texto(venda_fiscal.tipo_operacao),
        finalidade_operacao=_texto(
            venda_fiscal.finalidade_operacao
        ),
        contribuinte_icms=bool(
            venda_fiscal.contribuinte_icms
        ),
        consumidor_final=bool(
            venda_fiscal.consumidor_final
        ),
        total_base_operacao=venda_fiscal.total_base_operacao,
        total_base_icms=venda_fiscal.total_base_icms,
        total_icms=venda_fiscal.total_icms,
        total_fcp=venda_fiscal.total_fcp,
        total_base_pis=venda_fiscal.total_base_pis,
        total_pis=venda_fiscal.total_pis,
        total_base_cofins=venda_fiscal.total_base_cofins,
        total_cofins=venda_fiscal.total_cofins,
        total_base_ipi=venda_fiscal.total_base_ipi,
        total_ipi=venda_fiscal.total_ipi,
        total_tributos=venda_fiscal.total_tributos,
        itens=tuple(itens),
        emitente=_construir_emitente_documento_fiscal(venda),
        destinatario=_construir_destinatario_documento_fiscal(venda),
        pagamentos=_construir_pagamentos_documento_fiscal(venda),
    )


def validar_dados_documento_fiscal(*, dados):
    errors = {}

    if not dados.itens:
        errors["itens"] = (
            "Documento fiscal precisa possuir ao menos um item."
        )

    if dados.serie < 1:
        errors["serie"] = "A serie deve ser maior que zero."

    for indice, item in enumerate(dados.itens, start=1):
        prefixo = f"item_{indice}"

        if not item.ncm_codigo:
            errors[f"{prefixo}_ncm"] = (
                "Item fiscal sem NCM."
            )

        if not item.cfop_codigo:
            errors[f"{prefixo}_cfop"] = (
                "Item fiscal sem CFOP."
            )

        if not (
            item.cst_icms_codigo
            or item.csosn_codigo
        ):
            errors[f"{prefixo}_icms"] = (
                "Item fiscal sem CST ICMS ou CSOSN."
            )

        if item.quantidade <= 0:
            errors[f"{prefixo}_quantidade"] = (
                "Quantidade fiscal deve ser maior que zero."
            )

        if item.valor_produtos < 0:
            errors[f"{prefixo}_valor"] = (
                "Valor de produtos nao pode ser negativo."
            )

    if errors:
        raise ValidationError(errors)


def obter_ou_criar_documento_fiscal_rascunho(
    *,
    venda_fiscal,
    modelo,
    ambiente,
    serie,
):
    chave = gerar_idempotency_key_documento_fiscal(
        venda_fiscal_id=venda_fiscal.pk,
        modelo=modelo,
        ambiente=ambiente,
        serie=serie,
    )

    existente = DocumentoFiscal.objects.filter(
        idempotency_key=chave
    ).first()

    if existente is not None:
        return existente, False

    venda = venda_fiscal.venda

    try:
        with transaction.atomic():
            documento = DocumentoFiscal.objects.create(
                venda_fiscal=venda_fiscal,
                matriz_id=venda.matriz_id,
                loja_id=venda.loja_id,
                modelo=modelo,
                ambiente=ambiente,
                serie=serie,
                numero=None,
                idempotency_key=chave,
            )

        return documento, True
    except IntegrityError:
        documento = DocumentoFiscal.objects.get(
            idempotency_key=chave
        )

        return documento, False


@transaction.atomic
def preparar_documento_fiscal(
    *,
    venda_fiscal,
    modelo,
    ambiente,
    serie,
):
    _validar_parametros_preparacao(
        venda_fiscal=venda_fiscal,
        modelo=modelo,
        ambiente=ambiente,
        serie=serie,
    )

    documento, criado = (
        obter_ou_criar_documento_fiscal_rascunho(
            venda_fiscal=venda_fiscal,
            modelo=modelo,
            ambiente=ambiente,
            serie=serie,
        )
    )

    documento = (
        DocumentoFiscal.objects
        .select_for_update()
        .get(pk=documento.pk)
    )

    if documento.status == StatusDocumentoFiscal.PREPARADO:
        dados = construir_dados_documento_fiscal(
            venda_fiscal=venda_fiscal,
            modelo=documento.modelo,
            ambiente=documento.ambiente,
            serie=documento.serie,
            numero=documento.numero,
        )

        validar_dados_documento_fiscal(
            dados=dados
        )

        return documento, dados, criado

    if documento.status != StatusDocumentoFiscal.RASCUNHO:
        raise ValidationError({
            "status": (
                "Somente DocumentoFiscal em RASCUNHO pode "
                "ser preparado por este service."
            )
        })

    # A validacao do payload ocorre ANTES da reserva numerica.
    dados_sem_numero = construir_dados_documento_fiscal(
        venda_fiscal=venda_fiscal,
        modelo=documento.modelo,
        ambiente=documento.ambiente,
        serie=documento.serie,
        numero=documento.numero,
    )

    validar_dados_documento_fiscal(
        dados=dados_sem_numero
    )

    if documento.numero is None:
        documento.numero = (
            reservar_proximo_numero_documento_fiscal(
                matriz=documento.matriz,
                loja=documento.loja,
                modelo=documento.modelo,
                ambiente=documento.ambiente,
                serie=documento.serie,
            )
        )

    documento.full_clean()

    transicionar_documento_fiscal(
        documento=documento,
        novo_status=StatusDocumentoFiscal.PREPARADO,
        salvar=True,
    )

    dados_preparados = construir_dados_documento_fiscal(
        venda_fiscal=venda_fiscal,
        modelo=documento.modelo,
        ambiente=documento.ambiente,
        serie=documento.serie,
        numero=documento.numero,
    )

    validar_dados_documento_fiscal(
        dados=dados_preparados
    )

    return documento, dados_preparados, criado