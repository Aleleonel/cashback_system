from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from xml.etree import ElementTree as ET


NFE_NAMESPACE = "http://www.portalfiscal.inf.br/nfe"
NFE_VERSION = "4.00"

ET.register_namespace("", NFE_NAMESPACE)


class NFCeXMLError(ValueError):
    """Erro de construcao do XML da NFC-e."""


def _tag(nome: str) -> str:
    return f"{{{NFE_NAMESPACE}}}{nome}"


def format_decimal(value, casas: int = 2) -> str:
    """
    Formata valores numericos de forma deterministica para o XML fiscal.
    """
    decimal_value = Decimal(str(value))
    quantizer = Decimal("1").scaleb(-casas)

    return format(
        decimal_value.quantize(
            quantizer,
            rounding=ROUND_HALF_UP,
        ),
        f".{casas}f",
    )


def validar_chave_acesso(chave_acesso: str) -> str:
    """
    Executa validacao estrutural minima da chave de acesso.
    """
    chave = str(chave_acesso or "").strip()

    if len(chave) != 44:
        raise NFCeXMLError(
            "A chave de acesso da NFC-e deve possuir 44 digitos."
        )

    if not chave.isdigit():
        raise NFCeXMLError(
            "A chave de acesso da NFC-e deve conter somente digitos."
        )

    return chave


def criar_envelope_nfce(chave_acesso: str) -> ET.Element:
    """
    Cria o envelope estrutural inicial da NFC-e.
    """
    chave = validar_chave_acesso(chave_acesso)

    nfe = ET.Element(_tag("NFe"))

    ET.SubElement(
        nfe,
        _tag("infNFe"),
        {
            "versao": NFE_VERSION,
            "Id": f"NFe{chave}",
        },
    )

    return nfe


def serializar_xml(elemento: ET.Element) -> str:
    """
    Serializa o elemento XML em Unicode, sem declaracao XML.
    """
    return ET.tostring(
        elemento,
        encoding="unicode",
        short_empty_elements=True,
    )


def gerar_xml_nfce_basico(chave_acesso: str) -> str:
    """
    API publica inicial da etapa 195F1A.
    """
    return serializar_xml(
        criar_envelope_nfce(chave_acesso)
    )

# 195F1B_START
from datetime import datetime

from fiscal.services_chave_acesso import codigo_uf_ibge


def _texto_xml(value) -> str:
    return str(value or "").strip()


def _somente_digitos_xml(value) -> str:
    return "".join(ch for ch in _texto_xml(value) if ch.isdigit())


def _subelement_text(parent: ET.Element, nome: str, valor) -> ET.Element:
    element = ET.SubElement(parent, _tag(nome))
    element.text = str(valor)
    return element


def _validar_data_emissao(data_emissao: datetime) -> datetime:
    if not isinstance(data_emissao, datetime):
        raise NFCeXMLError("data_emissao deve ser datetime.")

    if data_emissao.tzinfo is None or data_emissao.utcoffset() is None:
        raise NFCeXMLError(
            "data_emissao deve possuir timezone para gerar dhEmi."
        )

    return data_emissao


def _tp_ambiente_xml(ambiente: str) -> str:
    valor = _texto_xml(ambiente).lower()

    if valor in {"producao", "produção", "1"}:
        return "1"

    if valor in {"homologacao", "homologação", "2"}:
        return "2"

    raise NFCeXMLError("Ambiente fiscal invalido para tpAmb.")


def _validar_documento_195f1b(documento) -> None:
    chave = validar_chave_acesso(getattr(documento, "chave_acesso", ""))

    modelo = _texto_xml(getattr(documento, "modelo", ""))
    if modelo != "65":
        raise NFCeXMLError("A 195F1B exige NFC-e modelo 65.")

    serie = getattr(documento, "serie", None)
    numero = getattr(documento, "numero", None)

    if not isinstance(serie, int) or serie < 1:
        raise NFCeXMLError("Serie fiscal invalida.")

    if not isinstance(numero, int) or numero < 1:
        raise NFCeXMLError("Numero fiscal invalido.")

    if len(chave) != 44:
        raise NFCeXMLError("Chave de acesso invalida.")


def adicionar_ide_nfce(
    inf_nfe: ET.Element,
    *,
    documento,
    dados,
    data_emissao: datetime,
    natureza_operacao: str = "VENDA",
    versao_processo: str = "ProCash",
) -> ET.Element:
    _validar_documento_195f1b(documento)
    data_emissao = _validar_data_emissao(data_emissao)

    emitente = getattr(dados, "emitente", None)
    if emitente is None:
        raise NFCeXMLError("Emitente obrigatorio para gerar ide.")

    uf = _texto_xml(getattr(emitente, "uf", "")).upper()
    codigo_municipio = _somente_digitos_xml(
        getattr(emitente, "codigo_municipio_ibge", "")
    )

    if len(codigo_municipio) != 7:
        raise NFCeXMLError("Codigo IBGE do municipio do emitente invalido.")

    cuf = str(codigo_uf_ibge(uf))
    chave = validar_chave_acesso(documento.chave_acesso)
    cnf = chave[35:43]
    cdv = chave[43]

    ide = ET.SubElement(inf_nfe, _tag("ide"))

    campos = (
        ("cUF", cuf),
        ("cNF", cnf),
        ("natOp", _texto_xml(natureza_operacao) or "VENDA"),
        ("mod", "65"),
        ("serie", documento.serie),
        ("nNF", documento.numero),
        ("dhEmi", data_emissao.isoformat(timespec="seconds")),
        ("tpNF", "1"),
        ("idDest", "1"),
        ("cMunFG", codigo_municipio),
        ("tpImp", "4"),
        ("tpEmis", "1"),
        ("cDV", cdv),
        ("tpAmb", _tp_ambiente_xml(getattr(documento, "ambiente", ""))),
        ("finNFe", "1"),
        ("indFinal", "1"),
        ("indPres", "1"),
        ("procEmi", "0"),
        ("verProc", _texto_xml(versao_processo) or "ProCash"),
    )

    for nome, valor in campos:
        _subelement_text(ide, nome, valor)

    return ide


def adicionar_emitente_nfce(
    inf_nfe: ET.Element,
    *,
    emitente,
    crt: str,
) -> ET.Element:
    if emitente is None:
        raise NFCeXMLError("Emitente obrigatorio.")

    cnpj = _somente_digitos_xml(getattr(emitente, "cnpj", ""))
    if len(cnpj) != 14:
        raise NFCeXMLError("CNPJ do emitente deve possuir 14 digitos.")

    ie = _texto_xml(getattr(emitente, "inscricao_estadual", ""))
    razao = _texto_xml(getattr(emitente, "razao_social", ""))
    fantasia = _texto_xml(getattr(emitente, "nome_fantasia", ""))

    if not razao:
        raise NFCeXMLError("Razao social do emitente obrigatoria.")

    if not ie:
        raise NFCeXMLError("Inscricao estadual do emitente obrigatoria.")

    crt = _texto_xml(crt)
    if crt not in {"1", "2", "3", "4"}:
        raise NFCeXMLError("CRT invalido.")

    emit = ET.SubElement(inf_nfe, _tag("emit"))
    _subelement_text(emit, "CNPJ", cnpj)
    _subelement_text(emit, "xNome", razao)

    if fantasia:
        _subelement_text(emit, "xFant", fantasia)

    ender = ET.SubElement(emit, _tag("enderEmit"))

    endereco = (
        ("xLgr", getattr(emitente, "logradouro", "")),
        ("nro", getattr(emitente, "numero", "")),
        ("xBairro", getattr(emitente, "bairro", "")),
        ("cMun", _somente_digitos_xml(
            getattr(emitente, "codigo_municipio_ibge", "")
        )),
        ("xMun", getattr(emitente, "municipio", "")),
        ("UF", _texto_xml(getattr(emitente, "uf", "")).upper()),
        ("CEP", _somente_digitos_xml(getattr(emitente, "cep", ""))),
        ("cPais", "1058"),
        ("xPais", "BRASIL"),
    )

    obrigatorios = {"xLgr", "nro", "xBairro", "cMun", "xMun", "UF"}

    for nome, valor in endereco:
        texto = _texto_xml(valor)
        if nome in obrigatorios and not texto:
            raise NFCeXMLError(
                f"Campo obrigatorio do endereco do emitente ausente: {nome}."
            )
        if texto:
            _subelement_text(ender, nome, texto)

    _subelement_text(emit, "IE", ie)
    _subelement_text(emit, "CRT", crt)

    return emit


def adicionar_destinatario_nfce(
    inf_nfe: ET.Element,
    *,
    destinatario,
    ambiente: str,
) -> ET.Element | None:
    if destinatario is None:
        return None

    documento = _somente_digitos_xml(
        getattr(destinatario, "cpf_cnpj", "")
    )

    nome = _texto_xml(getattr(destinatario, "nome", ""))
    email = _texto_xml(getattr(destinatario, "email", ""))

    if not documento and not nome and not email:
        return None

    dest = ET.SubElement(inf_nfe, _tag("dest"))

    if documento:
        if len(documento) == 11:
            _subelement_text(dest, "CPF", documento)
        elif len(documento) == 14:
            _subelement_text(dest, "CNPJ", documento)
        else:
            raise NFCeXMLError(
                "CPF/CNPJ do destinatario possui tamanho invalido."
            )

    if nome:
        _subelement_text(dest, "xNome", nome)

    if email:
        _subelement_text(dest, "email", email)

    return dest


def gerar_xml_nfce_195f1b(
    *,
    documento,
    dados,
    data_emissao: datetime,
    crt: str,
    natureza_operacao: str = "VENDA",
    versao_processo: str = "ProCash",
) -> str:
    _validar_documento_195f1b(documento)

    nfe = criar_envelope_nfce(documento.chave_acesso)
    inf_nfe = nfe.find(_tag("infNFe"))

    adicionar_ide_nfce(
        inf_nfe,
        documento=documento,
        dados=dados,
        data_emissao=data_emissao,
        natureza_operacao=natureza_operacao,
        versao_processo=versao_processo,
    )

    emitente = getattr(dados, "emitente", None)

    adicionar_emitente_nfce(
        inf_nfe,
        emitente=emitente,
        crt=crt,
    )

    adicionar_destinatario_nfce(
        inf_nfe,
        destinatario=getattr(dados, "destinatario", None),
        ambiente=getattr(documento, "ambiente", ""),
    )

    return serializar_xml(nfe)
# 195F1B_END

# 195F1C_START
from decimal import Decimal, InvalidOperation


def _decimal_xml(valor, *, casas=2) -> Decimal:
    try:
        numero = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError):
        raise NFCeXMLError("Valor decimal invalido.")
    if numero < 0:
        raise NFCeXMLError("Valor decimal nao pode ser negativo.")
    return numero


def _attr_xml(objeto, *nomes, default=""):
    for nome in nomes:
        if hasattr(objeto, nome):
            valor = getattr(objeto, nome)
            if valor is not None:
                return valor
    return default


def _codigo_pagamento_nfce(pagamento) -> str:
    tipo = _texto_xml(_attr_xml(pagamento, "tipo", "codigo")).lower()
    codigo = _texto_xml(_attr_xml(pagamento, "codigo")).upper()

    mapa = {
        "dinheiro": "01",
        "pix": "17",
        "cartao_credito": "03",
        "cartão_credito": "03",
        "credito": "03",
        "crédito": "03",
        "cartao_debito": "04",
        "cartão_debito": "04",
        "debito": "04",
        "débito": "04",
    }
    mapa_codigo = {
        "DINHEIRO": "01",
        "PIX": "17",
        "CREDITO": "03",
        "DEBITO": "04",
    }

    if tipo in mapa:
        return mapa[tipo]
    if codigo in mapa_codigo:
        return mapa_codigo[codigo]

    raise NFCeXMLError(
        "Forma de pagamento sem codigo NFC-e suportado na 195F1C."
    )


def adicionar_detalhes_produtos_nfce(inf_nfe: ET.Element, *, itens):
    itens = tuple(itens or ())
    if not itens:
        raise NFCeXMLError("A NFC-e deve possuir ao menos um item.")

    for indice, item in enumerate(itens, start=1):
        codigo = _texto_xml(_attr_xml(
            item, "codigo", "codigo_produto", "produto_codigo"
        ))
        descricao = _texto_xml(_attr_xml(
            item, "descricao", "descricao_produto", "produto_descricao"
        ))
        ncm = _somente_digitos_xml(_attr_xml(item, "ncm_codigo", "ncm"))
        cest = _somente_digitos_xml(_attr_xml(item, "cest_codigo", "cest"))
        cfop = _somente_digitos_xml(_attr_xml(item, "cfop_codigo", "cfop"))
        unidade = _texto_xml(_attr_xml(
            item, "unidade_comercial", "unidade", default="UN"
        )).upper()
        gtin = _somente_digitos_xml(_attr_xml(item, "gtin"))

        quantidade = _decimal_xml(_attr_xml(item, "quantidade"))
        valor_unitario = _decimal_xml(_attr_xml(item, "valor_unitario"))
        valor_produtos = _decimal_xml(_attr_xml(item, "valor_produtos"))
        desconto = _decimal_xml(_attr_xml(item, "desconto", default=0))
        frete = _decimal_xml(_attr_xml(item, "frete", default=0))
        seguro = _decimal_xml(_attr_xml(item, "seguro", default=0))
        outras = _decimal_xml(_attr_xml(item, "outras_despesas", default=0))

        if not codigo or not descricao:
            raise NFCeXMLError("Codigo e descricao do produto sao obrigatorios.")
        if len(ncm) != 8:
            raise NFCeXMLError("NCM deve possuir 8 digitos.")
        if len(cfop) != 4:
            raise NFCeXMLError("CFOP deve possuir 4 digitos.")
        if quantidade <= 0:
            raise NFCeXMLError("Quantidade deve ser maior que zero.")

        det = ET.SubElement(inf_nfe, _tag("det"), {"nItem": str(indice)})
        prod = ET.SubElement(det, _tag("prod"))

        _subelement_text(prod, "cProd", codigo)
        _subelement_text(prod, "cEAN", gtin or "SEM GTIN")
        _subelement_text(prod, "xProd", descricao)
        _subelement_text(prod, "NCM", ncm)
        if cest:
            _subelement_text(prod, "CEST", cest)
        _subelement_text(prod, "CFOP", cfop)
        _subelement_text(prod, "uCom", unidade)
        _subelement_text(prod, "qCom", format_decimal(quantidade, 4))
        _subelement_text(prod, "vUnCom", format_decimal(valor_unitario, 10))
        _subelement_text(prod, "vProd", format_decimal(valor_produtos, 2))
        _subelement_text(prod, "cEANTrib", gtin or "SEM GTIN")
        _subelement_text(prod, "uTrib", unidade)
        _subelement_text(prod, "qTrib", format_decimal(quantidade, 4))
        _subelement_text(prod, "vUnTrib", format_decimal(valor_unitario, 10))

        if frete:
            _subelement_text(prod, "vFrete", format_decimal(frete, 2))
        if seguro:
            _subelement_text(prod, "vSeg", format_decimal(seguro, 2))
        if desconto:
            _subelement_text(prod, "vDesc", format_decimal(desconto, 2))
        if outras:
            _subelement_text(prod, "vOutro", format_decimal(outras, 2))

        _subelement_text(prod, "indTot", "1")

        # O grupo imposto sera preenchido na 195F2.
        imposto = ET.SubElement(det, _tag("imposto"))
        adicionar_icms_item_nfce(imposto, item=item)
        adicionar_pis_item_nfce(imposto, item=item)
        adicionar_cofins_item_nfce(imposto, item=item)


def adicionar_total_nfce(inf_nfe: ET.Element, *, itens):
    itens = tuple(itens or ())
    v_prod = sum((_decimal_xml(_attr_xml(i, "valor_produtos")) for i in itens), Decimal("0"))
    v_desc = sum((_decimal_xml(_attr_xml(i, "desconto", default=0)) for i in itens), Decimal("0"))
    v_frete = sum((_decimal_xml(_attr_xml(i, "frete", default=0)) for i in itens), Decimal("0"))
    v_seg = sum((_decimal_xml(_attr_xml(i, "seguro", default=0)) for i in itens), Decimal("0"))
    v_outro = sum((_decimal_xml(_attr_xml(i, "outras_despesas", default=0)) for i in itens), Decimal("0"))

    # 195F2A4C2 - totais ICMS derivados exclusivamente do snapshot/DTO.
    # O serializador nao recalcula base, aliquota ou imposto.
    v_bc = sum(
        (_decimal_xml(_attr_xml(i, "base_icms", default=0)) for i in itens),
        Decimal("0"),
    )
    v_icms = sum(
        (_decimal_xml(_attr_xml(i, "valor_icms", default=0)) for i in itens),
        Decimal("0"),
    )
    # 195F2B3 - totais PIS/COFINS exclusivamente do snapshot/DTO.
    v_pis = sum((_decimal_xml(_attr_xml(i, "valor_pis", default=0)) for i in itens), Decimal("0"))
    v_cofins = sum((_decimal_xml(_attr_xml(i, "valor_cofins", default=0)) for i in itens), Decimal("0"))
    v_nf = v_prod - v_desc + v_frete + v_seg + v_outro

    if v_nf < 0:
        raise NFCeXMLError("Total da NFC-e nao pode ser negativo.")

    total = ET.SubElement(inf_nfe, _tag("total"))
    # 195F2C2A_START - total FCP congelado
    v_fcp = sum(
        (_decimal_xml(_attr_xml(i, "valor_fcp", default=0)) for i in itens),
        Decimal("0"),
    )
    # 195F2C2A_END - total FCP congelado

    icms = ET.SubElement(total, _tag("ICMSTot"))

    campos = (
        ("vBC", v_bc), ("vICMS", v_icms), ("vICMSDeson", 0), ("vFCP", v_fcp),
        ("vBCST", 0), ("vST", 0), ("vFCPST", 0), ("vFCPSTRet", 0),
        ("vProd", v_prod), ("vFrete", v_frete), ("vSeg", v_seg),
        ("vDesc", v_desc), ("vII", 0), ("vIPI", 0), ("vIPIDevol", 0),
        ("vPIS", v_pis), ("vCOFINS", v_cofins), ("vOutro", v_outro), ("vNF", v_nf),
    )
    for nome, valor in campos:
        _subelement_text(icms, nome, format_decimal(valor, 2))

    return v_nf


# 195F2E3_START - Transporte minimo NFC-e
def adicionar_transporte_nfce(inf_nfe: ET.Element):
    """
    Serializa o grupo X de transporte para a NFC-e atual.

    O contrato fiscal vigente exige o grupo transp e o campo modFrete.
    Enquanto o sistema nao possuir contrato proprio de entrega/transporte,
    a NFC-e e emitida sem ocorrencia de transporte (modFrete=9).
    """
    transp = ET.SubElement(inf_nfe, _tag("transp"))
    _subelement_text(transp, "modFrete", "9")
    return transp


# 195F2E3_END - Transporte minimo NFC-e
def adicionar_pagamentos_nfce(inf_nfe: ET.Element, *, pagamentos):
    pagamentos = tuple(pagamentos or ())
    if not pagamentos:
        raise NFCeXMLError("A NFC-e deve possuir ao menos um pagamento.")

    pag = ET.SubElement(inf_nfe, _tag("pag"))
    total_troco = Decimal("0")

    for pagamento in pagamentos:
        valor = _decimal_xml(_attr_xml(pagamento, "valor"))
        troco = _decimal_xml(_attr_xml(pagamento, "troco", default=0))
        total_troco += troco

        det_pag = ET.SubElement(pag, _tag("detPag"))
        _subelement_text(det_pag, "tPag", _codigo_pagamento_nfce(pagamento))
        _subelement_text(det_pag, "vPag", format_decimal(valor, 2))

    if total_troco:
        _subelement_text(pag, "vTroco", format_decimal(total_troco, 2))

    return pag


def gerar_xml_nfce_195f1c(
    *,
    documento,
    dados,
    data_emissao: datetime,
    crt: str,
    natureza_operacao: str = "VENDA",
    versao_processo: str = "ProCash",
) -> str:
    _validar_documento_195f1b(documento)
    nfe = criar_envelope_nfce(documento.chave_acesso)
    inf_nfe = nfe.find(_tag("infNFe"))

    adicionar_ide_nfce(
        inf_nfe, documento=documento, dados=dados,
        data_emissao=data_emissao,
        natureza_operacao=natureza_operacao,
        versao_processo=versao_processo,
    )
    adicionar_emitente_nfce(
        inf_nfe, emitente=getattr(dados, "emitente", None), crt=crt
    )
    adicionar_destinatario_nfce(
        inf_nfe,
        destinatario=getattr(dados, "destinatario", None),
        ambiente=getattr(documento, "ambiente", ""),
    )
    adicionar_detalhes_produtos_nfce(
        inf_nfe, itens=getattr(dados, "itens", ())
    )
    adicionar_total_nfce(inf_nfe, itens=getattr(dados, "itens", ()))
    adicionar_transporte_nfce(inf_nfe)
    adicionar_pagamentos_nfce(
        inf_nfe, pagamentos=getattr(dados, "pagamentos", ())
    )
    return serializar_xml(nfe)
# 195F1C_END
# 195F2A2_START
def adicionar_icms_item_nfce(imposto: ET.Element, *, item):
    """
    Serializa exclusivamente ICMS CST 00.

    Regras desta etapa:
    - item sem CST/CSOSN: nao serializa ICMS, preservando compatibilidade
      estrutural da 195F1C;
    - CSOSN: ainda nao suportado nesta etapa;
    - CST diferente de 00: ainda nao suportado nesta etapa;
    - nenhum calculo tributario e realizado aqui.
    """
    cst = _texto_xml(_attr_xml(item, "cst_icms_codigo"))
    csosn = _texto_xml(_attr_xml(item, "csosn_codigo"))
    regime = _texto_xml(_attr_xml(item, "regime_tributario")).lower()

    if not cst and not csosn:
        return None

    if cst and csosn:
        raise NFCeXMLError(
            "Item fiscal nao pode possuir CST ICMS e CSOSN simultaneamente."
        )

    if csosn:
        raise NFCeXMLError(
            "CSOSN ainda nao suportado pela 195F2A2."
        )

    if cst != "00":
        raise NFCeXMLError(
            f"CST ICMS {cst} ainda nao suportado pela 195F2A2."
        )

    if regime and regime != "normal":
        raise NFCeXMLError(
            "CST 00 exige regime tributario normal."
        )

    origem = _texto_xml(_attr_xml(item, "origem_mercadoria_codigo"))
    mod_bc = _texto_xml(_attr_xml(item, "modalidade_base_icms"))
    aliquota = _attr_xml(item, "aliquota_icms", default=None)
    base_icms = _attr_xml(item, "base_icms", default=None)
    valor_icms = _attr_xml(item, "valor_icms", default=None)

    if origem not in {str(i) for i in range(9)}:
        raise NFCeXMLError(
            "Origem da mercadoria invalida para ICMS00."
        )

    if mod_bc not in {"0", "1", "2", "3"}:
        raise NFCeXMLError(
            "modBC invalido para ICMS00."
        )

    if aliquota is None:
        raise NFCeXMLError(
            "Aliquota ICMS obrigatoria para ICMS00."
        )

    if base_icms is None:
        raise NFCeXMLError(
            "Base ICMS obrigatoria para ICMS00."
        )

    if valor_icms is None:
        raise NFCeXMLError(
            "Valor ICMS obrigatorio para ICMS00."
        )

    base_icms = _decimal_xml(base_icms)
    aliquota = _decimal_xml(aliquota)
    valor_icms = _decimal_xml(valor_icms)

    icms = ET.SubElement(imposto, _tag("ICMS"))
    # 195F2C2A_START - FCP CST00 congelado
    base_fcp = _decimal_xml(_attr_xml(item, "base_fcp", default=0))
    aliquota_fcp_raw = _attr_xml(item, "aliquota_fcp", default=None)
    valor_fcp = _decimal_xml(_attr_xml(item, "valor_fcp", default=0))

    possui_fcp = (
        base_fcp != Decimal("0")
        or valor_fcp != Decimal("0")
        or aliquota_fcp_raw not in (None, "")
    )

    aliquota_fcp = None
    if possui_fcp:
        if aliquota_fcp_raw in (None, ""):
            raise NFCeXMLError("Aliquota FCP obrigatoria para ICMS00 quando houver FCP.")
        aliquota_fcp = _decimal_xml(aliquota_fcp_raw)
        if base_fcp <= Decimal("0"):
            raise NFCeXMLError("Base FCP obrigatoria para ICMS00 quando houver FCP.")
        if aliquota_fcp <= Decimal("0"):
            raise NFCeXMLError("Aliquota FCP deve ser maior que zero para ICMS00.")
        if valor_fcp < Decimal("0"):
            raise NFCeXMLError("Valor FCP invalido para ICMS00.")
    # 195F2C2A_END - FCP CST00 congelado

    icms00 = ET.SubElement(icms, _tag("ICMS00"))

    _subelement_text(icms00, "orig", origem)
    _subelement_text(icms00, "CST", "00")
    _subelement_text(icms00, "modBC", mod_bc)
    _subelement_text(icms00, "vBC", format_decimal(base_icms, 2))
    _subelement_text(icms00, "pICMS", format_decimal(aliquota, 4))
    _subelement_text(icms00, "vICMS", format_decimal(valor_icms, 2))
    # 195F2C2A_START - campos FCP CST00
    if possui_fcp:

        _subelement_text(icms00, "pFCP", format_decimal(aliquota_fcp, 4))
        _subelement_text(icms00, "vFCP", format_decimal(valor_fcp, 2))
    # 195F2C2A_END - campos FCP CST00

    return icms00
# 195F2A2_END

# 195F2B2_START
def adicionar_pis_item_nfce(imposto: ET.Element, *, item):
    """Serializa exclusivamente PIS CST 01 (PISAliq), sem recalculo."""
    cst = _texto_xml(_attr_xml(item, "cst_pis_codigo"))
    if not cst:
        return None
    if cst != "01":
        raise NFCeXMLError(f"CST PIS {cst} ainda nao suportado pela 195F2B2.")

    base = _attr_xml(item, "base_pis", default=None)
    aliquota = _attr_xml(item, "aliquota_pis", default=None)
    valor = _attr_xml(item, "valor_pis", default=None)
    if base is None:
        raise NFCeXMLError("Base PIS obrigatoria para PIS CST 01.")
    if aliquota is None:
        raise NFCeXMLError("Aliquota PIS obrigatoria para PIS CST 01.")
    if valor is None:
        raise NFCeXMLError("Valor PIS obrigatorio para PIS CST 01.")

    base = _decimal_xml(base)
    aliquota = _decimal_xml(aliquota)
    valor = _decimal_xml(valor)
    pis = ET.SubElement(imposto, _tag("PIS"))
    pis_aliq = ET.SubElement(pis, _tag("PISAliq"))
    _subelement_text(pis_aliq, "CST", "01")
    _subelement_text(pis_aliq, "vBC", format_decimal(base, 2))
    _subelement_text(pis_aliq, "pPIS", format_decimal(aliquota, 4))
    _subelement_text(pis_aliq, "vPIS", format_decimal(valor, 2))
    return pis_aliq


def adicionar_cofins_item_nfce(imposto: ET.Element, *, item):
    """Serializa exclusivamente COFINS CST 01 (COFINSAliq), sem recalculo."""
    cst = _texto_xml(_attr_xml(item, "cst_cofins_codigo"))
    if not cst:
        return None
    if cst != "01":
        raise NFCeXMLError(f"CST COFINS {cst} ainda nao suportado pela 195F2B2.")

    base = _attr_xml(item, "base_cofins", default=None)
    aliquota = _attr_xml(item, "aliquota_cofins", default=None)
    valor = _attr_xml(item, "valor_cofins", default=None)
    if base is None:
        raise NFCeXMLError("Base COFINS obrigatoria para COFINS CST 01.")
    if aliquota is None:
        raise NFCeXMLError("Aliquota COFINS obrigatoria para COFINS CST 01.")
    if valor is None:
        raise NFCeXMLError("Valor COFINS obrigatorio para COFINS CST 01.")

    base = _decimal_xml(base)
    aliquota = _decimal_xml(aliquota)
    valor = _decimal_xml(valor)
    cofins = ET.SubElement(imposto, _tag("COFINS"))
    cofins_aliq = ET.SubElement(cofins, _tag("COFINSAliq"))
    _subelement_text(cofins_aliq, "CST", "01")
    _subelement_text(cofins_aliq, "vBC", format_decimal(base, 2))
    _subelement_text(cofins_aliq, "pCOFINS", format_decimal(aliquota, 4))
    _subelement_text(cofins_aliq, "vCOFINS", format_decimal(valor, 2))
    return cofins_aliq
# 195F2B2_END
