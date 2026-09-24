import csv
import io
from collections import OrderedDict
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction

from financeiro.models import CentroCusto, PlanoConta, TituloFinanceiro
from financeiro.services import criar_lancamento_manual


CAMPOS_CSV = [
    "chave_idempotencia",
    "descricao",
    "entidade_nome",
    "documento_referencia",
    "data_emissao",
    "data_competencia",
    "plano_conta_codigo",
    "centro_custo_codigo",
    "valor_bruto",
    "valor_desconto",
    "valor_juros",
    "observacao",
    "parcela_numero",
    "parcela_vencimento",
    "parcela_valor",
]

CAMPOS_TITULO = [
    "descricao",
    "entidade_nome",
    "documento_referencia",
    "data_emissao",
    "data_competencia",
    "plano_conta_codigo",
    "centro_custo_codigo",
    "valor_bruto",
    "valor_desconto",
    "valor_juros",
    "observacao",
]


def _erro(linha, campo, mensagem):
    raise ValidationError(f"Linha {linha}, campo {campo}: {mensagem}")


def _decimal(valor, linha, campo, *, obrigatorio=False):
    texto = (valor or "").strip().replace(",", ".")
    if not texto:
        if obrigatorio:
            _erro(linha, campo, "valor obrigatorio.")
        return Decimal("0.00")
    try:
        numero = Decimal(texto)
    except InvalidOperation:
        _erro(linha, campo, "decimal invalido.")
    return numero


def _data(valor, linha, campo, *, obrigatorio=False):
    texto = (valor or "").strip()
    if not texto:
        if obrigatorio:
            _erro(linha, campo, "data obrigatoria no formato AAAA-MM-DD.")
        return None
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except ValueError:
        _erro(linha, campo, "data invalida; use AAAA-MM-DD.")


def _inteiro_positivo(valor, linha, campo):
    try:
        numero = int((valor or "").strip())
    except (TypeError, ValueError):
        _erro(linha, campo, "inteiro positivo obrigatorio.")
    if numero <= 0:
        _erro(linha, campo, "deve ser maior que zero.")
    return numero


def _texto_linha(row):
    return {campo: (row.get(campo) or "").strip() for campo in CAMPOS_CSV}


def _validar_cabecalho(fieldnames):
    recebido = list(fieldnames or [])
    if recebido != CAMPOS_CSV:
        raise ValidationError(
            "Cabecalho CSV invalido. Use exatamente: " + ";".join(CAMPOS_CSV)
        )


def _ler_e_validar(arquivo, matriz):
    try:
        bruto = arquivo.read()
        if isinstance(bruto, bytes):
            texto = bruto.decode("utf-8-sig")
        else:
            texto = str(bruto)
    except UnicodeDecodeError as exc:
        raise ValidationError("Arquivo CSV deve estar em UTF-8.") from exc

    reader = csv.DictReader(io.StringIO(texto), delimiter=";")
    _validar_cabecalho(reader.fieldnames)
    grupos = OrderedDict()

    for linha, row in enumerate(reader, start=2):
        dados = _texto_linha(row)
        chave = dados["chave_idempotencia"]
        if not chave:
            _erro(linha, "chave_idempotencia", "campo obrigatorio.")
        if not dados["descricao"]:
            _erro(linha, "descricao", "campo obrigatorio.")
        if not dados["plano_conta_codigo"]:
            _erro(linha, "plano_conta_codigo", "campo obrigatorio.")

        normalizado = {
            **dados,
            "_linha": linha,
            "_data_emissao": _data(dados["data_emissao"], linha, "data_emissao", obrigatorio=True),
            "_data_competencia": _data(dados["data_competencia"], linha, "data_competencia"),
            "_valor_bruto": _decimal(dados["valor_bruto"], linha, "valor_bruto", obrigatorio=True),
            "_valor_desconto": _decimal(dados["valor_desconto"], linha, "valor_desconto"),
            "_valor_juros": _decimal(dados["valor_juros"], linha, "valor_juros"),
            "_parcela_numero": _inteiro_positivo(dados["parcela_numero"], linha, "parcela_numero"),
            "_parcela_vencimento": _data(dados["parcela_vencimento"], linha, "parcela_vencimento", obrigatorio=True),
            "_parcela_valor": _decimal(dados["parcela_valor"], linha, "parcela_valor", obrigatorio=True),
        }
        if normalizado["_valor_bruto"] <= 0:
            _erro(linha, "valor_bruto", "deve ser maior que zero.")
        if normalizado["_parcela_valor"] <= 0:
            _erro(linha, "parcela_valor", "deve ser maior que zero.")

        grupo = grupos.setdefault(chave, {"base": normalizado, "linhas": []})
        base = grupo["base"]
        for campo in CAMPOS_TITULO:
            if dados[campo] != base[campo]:
                _erro(linha, campo, "diverge das demais linhas da mesma chave_idempotencia.")
        grupo["linhas"].append(normalizado)

    if not grupos:
        raise ValidationError("O arquivo CSV nao possui linhas de dados.")

    preparados = []
    for chave, grupo in grupos.items():
        base = grupo["base"]
        linhas = grupo["linhas"]
        numeros = [item["_parcela_numero"] for item in linhas]
        if len(numeros) != len(set(numeros)):
            _erro(base["_linha"], "parcela_numero", "numero de parcela duplicado na mesma chave.")

        try:
            plano = PlanoConta.objects.get(matriz=matriz, codigo=base["plano_conta_codigo"])
        except PlanoConta.DoesNotExist:
            _erro(base["_linha"], "plano_conta_codigo", "codigo nao encontrado na matriz.")

        centro = None
        if base["centro_custo_codigo"]:
            try:
                centro = CentroCusto.objects.get(matriz=matriz, codigo=base["centro_custo_codigo"])
            except CentroCusto.DoesNotExist:
                _erro(base["_linha"], "centro_custo_codigo", "codigo nao encontrado na matriz.")

        parcelas = [
            {
                "numero": item["_parcela_numero"],
                "vencimento": item["_parcela_vencimento"],
                "valor": item["_parcela_valor"],
            }
            for item in sorted(linhas, key=lambda item: item["_parcela_numero"])
        ]
        valor_final = base["_valor_bruto"] - base["_valor_desconto"] + base["_valor_juros"]
        if sum((p["valor"] for p in parcelas), Decimal("0.00")) != valor_final:
            _erro(base["_linha"], "parcela_valor", "soma das parcelas difere do valor final do titulo.")

        preparados.append({
            "chave": chave,
            "base": base,
            "plano": plano,
            "centro": centro,
            "parcelas": parcelas,
        })
    return preparados


@transaction.atomic
def importar_titulos_csv(*, arquivo, matriz, loja, usuario=None, request=None):
    preparados = _ler_e_validar(arquivo, matriz)
    titulos = []
    for item in preparados:
        base = item["base"]
        titulo = criar_lancamento_manual(
            matriz=matriz,
            loja=loja,
            natureza=TituloFinanceiro.Natureza.PAGAR,
            chave_idempotencia=f"csv:{item['chave']}",
            descricao=base["descricao"],
            data_emissao=base["_data_emissao"],
            parcelas=item["parcelas"],
            plano_conta=item["plano"],
            centro_custo=item["centro"],
            entidade_nome=base["entidade_nome"],
            documento_referencia=base["documento_referencia"],
            data_competencia=base["_data_competencia"],
            valor_bruto=base["_valor_bruto"],
            valor_desconto=base["_valor_desconto"],
            valor_juros=base["_valor_juros"],
            observacao=base["observacao"],
            usuario=usuario,
            request=request,
        )
        titulos.append(titulo)
    return {
        "titulos": titulos,
        "quantidade_titulos": len(titulos),
        "quantidade_parcelas": sum(len(item["parcelas"]) for item in preparados),
    }