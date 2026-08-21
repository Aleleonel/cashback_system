from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import date, datetime

from django.core.exceptions import ValidationError

CODIGOS_UF_IBGE = {
    "RO": "11", "AC": "12", "AM": "13", "RR": "14", "PA": "15", "AP": "16",
    "TO": "17", "MA": "21", "PI": "22", "CE": "23", "RN": "24", "PB": "25",
    "PE": "26", "AL": "27", "SE": "28", "BA": "29", "MG": "31", "ES": "32",
    "RJ": "33", "SP": "35", "PR": "41", "SC": "42", "RS": "43", "MS": "50",
    "MT": "51", "GO": "52", "DF": "53",
}

@dataclass(frozen=True, slots=True)
class IdentificacaoChaveAcesso:
    chave_acesso: str
    codigo_numerico: str
    digito_verificador: str

def somente_digitos(valor):
    return "".join(ch for ch in str(valor or "") if ch.isdigit())

def codigo_uf_ibge(uf):
    codigo = CODIGOS_UF_IBGE.get(str(uf or "").strip().upper())
    if not codigo:
        raise ValidationError({"uf": "UF invalida para composicao da chave de acesso."})
    return codigo

def aamm_data_emissao(data_emissao):
    if not isinstance(data_emissao, (date, datetime)):
        raise ValidationError({"data_emissao": "Data de emissao invalida."})
    return f"{data_emissao.year % 100:02d}{data_emissao.month:02d}"

def calcular_digito_verificador_chave(base_43):
    base_43 = str(base_43 or "").strip()
    if len(base_43) != 43 or not base_43.isdigit():
        raise ValidationError({"chave_acesso": "A base da chave deve conter exatamente 43 digitos."})
    soma = 0
    peso = 2
    for digito in reversed(base_43):
        soma += int(digito) * peso
        peso += 1
        if peso > 9:
            peso = 2
    dv = 11 - (soma % 11)
    return str(0 if dv >= 10 else dv)

def gerar_codigo_numerico():
    return f"{secrets.randbelow(100_000_000):08d}"

def construir_chave_acesso(*, uf, data_emissao, cnpj, modelo, serie, numero,
                           codigo_numerico, tipo_emissao="1"):
    cuf = codigo_uf_ibge(uf)
    aamm = aamm_data_emissao(data_emissao)
    cnpj = somente_digitos(cnpj)
    modelo = str(modelo or "").strip()
    tipo_emissao = str(tipo_emissao or "").strip()
    codigo_numerico = str(codigo_numerico or "").strip()
    errors = {}
    if len(cnpj) != 14:
        errors["cnpj"] = "O CNPJ do emitente deve possuir 14 digitos."
    if len(modelo) != 2 or not modelo.isdigit():
        errors["modelo"] = "O modelo fiscal deve possuir 2 digitos."
    if not isinstance(serie, int) or not 1 <= serie <= 999:
        errors["serie"] = "A serie deve estar entre 1 e 999."
    if not isinstance(numero, int) or not 1 <= numero <= 999_999_999:
        errors["numero"] = "O numero fiscal deve estar entre 1 e 999999999."
    if len(tipo_emissao) != 1 or not tipo_emissao.isdigit():
        errors["tipo_emissao"] = "O tipo de emissao deve possuir 1 digito."
    if len(codigo_numerico) != 8 or not codigo_numerico.isdigit():
        errors["codigo_numerico"] = "O codigo numerico deve possuir 8 digitos."
    if errors:
        raise ValidationError(errors)
    base = (f"{cuf}{aamm}{cnpj}{modelo}{serie:03d}{numero:09d}"
            f"{tipo_emissao}{codigo_numerico}")
    dv = calcular_digito_verificador_chave(base)
    return IdentificacaoChaveAcesso(base + dv, codigo_numerico, dv)

def identificar_documento_fiscal_nfce(*, documento, data_emissao,
                                      codigo_numerico=None, tipo_emissao="1"):
    if str(documento.modelo) != "65":
        raise ValidationError({"modelo": "A identificacao desta etapa exige NFC-e modelo 65."})
    if documento.numero is None:
        raise ValidationError({"numero": "Documento fiscal precisa possuir numero reservado."})
    try:
        configuracao = documento.loja.configuracao_emissao_fiscal
    except Exception as exc:
        raise ValidationError({"configuracao_emissao_fiscal": "Loja sem configuracao fiscal de emissao."}) from exc
    if not configuracao.ativa:
        raise ValidationError({"configuracao_emissao_fiscal": "Configuracao fiscal da loja esta inativa."})
    cnf = codigo_numerico or documento.codigo_numerico or gerar_codigo_numerico()
    identificacao = construir_chave_acesso(
        uf=configuracao.uf, data_emissao=data_emissao, cnpj=documento.loja.cnpj,
        modelo=documento.modelo, serie=documento.serie, numero=documento.numero,
        tipo_emissao=tipo_emissao, codigo_numerico=cnf,
    )
    documento.codigo_numerico = identificacao.codigo_numerico
    documento.digito_verificador = identificacao.digito_verificador
    documento.chave_acesso = identificacao.chave_acesso
    documento.full_clean()
    documento.save(update_fields=("codigo_numerico", "digito_verificador",
                                  "chave_acesso", "atualizado_em"))
    return identificacao
