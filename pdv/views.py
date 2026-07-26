from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from pdv.choices import (
    StatusCaixa,
    StatusOperacaoVenda,
    StatusSessaoCaixa,
    TipoMovimentacaoCaixa,
)
from pdv.models import (
    Caixa,
    ItemVenda,
    MovimentacaoCaixa,
    SessaoCaixa,
    Venda,
)
from pdv.services.cliente_consumidor import obter_ou_criar_cliente_consumidor
from pdv.services.vendas import (
    adicionar_item_venda,
    alterar_item_venda,
    cancelar_item_venda,
)
from produtos.models import Produto
from produtos.selectors.produtos import get_produto, get_produto_por_codigo, get_produtos


def _erro_validacao(exc):
    if hasattr(exc, "message_dict"):
        mensagens = []
        for valores in exc.message_dict.values():
            mensagens.extend(valores)
        return " ".join(mensagens)
    return " ".join(exc.messages) if hasattr(exc, "messages") else str(exc)


def _contexto_operacional(request):
    matriz = getattr(request.user, "matriz", None)
    if matriz is None:
        return None, None, None

    lojas = getattr(request.user, "lojas", None)
    loja = lojas.order_by("nome").first() if lojas is not None else None
    if loja is None:
        return matriz, None, None

    sessao = (
        SessaoCaixa.objects.select_related("caixa", "caixa__loja")
        .filter(
            caixa__loja=loja,
            status=StatusSessaoCaixa.ABERTA,
        )
        .order_by("-aberta_em")
        .first()
    )
    return matriz, loja, sessao


def _obter_venda_atual(request, *, criar=False):
    matriz, loja, sessao = _contexto_operacional(request)
    if not matriz or not loja or not sessao:
        return None, matriz, loja, sessao

    venda = (
        Venda.objects.select_related(
            "matriz",
            "loja",
            "sessao_caixa",
            "cliente",
            "operador",
            "vendedor",
        )
        .filter(
            matriz=matriz,
            loja=loja,
            sessao_caixa=sessao,
            operador=request.user,
            status__in=[
                StatusOperacaoVenda.RASCUNHO,
                StatusOperacaoVenda.ABERTA,
            ],
        )
        .order_by("-criada_em")
        .first()
    )

    if venda is None and criar:
        cliente = obter_ou_criar_cliente_consumidor(matriz=matriz, loja=loja)
        venda = Venda.objects.create(
            matriz=matriz,
            loja=loja,
            sessao_caixa=sessao,
            cliente=cliente,
            operador=request.user,
            vendedor=request.user,
            status=StatusOperacaoVenda.RASCUNHO,
        )

    return venda, matriz, loja, sessao


def _serializar_item(item):
    return {
        "id": item.pk,
        "produto": item.produto.nome,
        "codigo": item.produto.codigo_interno,
        "quantidade": str(item.quantidade),
        "preco_unitario": str(item.preco_unitario),
        "desconto": str(item.desconto),
        "subtotal": str(item.subtotal),
        "total": str(item.total),
    }


def _serializar_venda(venda):
    if venda is None:
        return {
            "id": None,
            "quantidade_itens": "0.000",
            "subtotal": "0.00",
            "desconto": "0.00",
            "acrescimo": "0.00",
            "total": "0.00",
            "itens": [],
        }

    venda.refresh_from_db()
    itens = (
        venda.itens.filter(cancelado=False)
        .select_related("produto")
        .order_by("sequencia")
    )
    return {
        "id": venda.pk,
        "quantidade_itens": str(venda.quantidade_itens),
        "subtotal": str(venda.subtotal),
        "desconto": str(venda.desconto),
        "acrescimo": str(venda.acrescimo),
        "total": str(venda.total),
        "itens": [_serializar_item(item) for item in itens],
    }


@login_required
@require_GET
def abrir_caixa(request):
    matriz, loja, sessao = _contexto_operacional(request)

    if not matriz or not loja:
        messages.error(
            request,
            "Seu usuário não possui matriz e loja operacional vinculadas.",
        )
        return redirect("pdv:inicio")

    if sessao:
        messages.info(request, "Já existe uma sessão de caixa aberta nesta loja.")
        return redirect("pdv:inicio")

    caixas = (
        Caixa.objects.filter(
            matriz=matriz,
            loja=loja,
            status=StatusCaixa.ATIVO,
        )
        .exclude(sessoes__status=StatusSessaoCaixa.ABERTA)
        .order_by("nome")
    )

    return render(
        request,
        "pdv/abrir_caixa.html",
        {
            "loja": loja,
            "caixas": caixas,
        },
    )


@login_required
@require_POST
def confirmar_abertura_caixa(request):
    matriz, loja, sessao = _contexto_operacional(request)

    if not matriz or not loja:
        messages.error(
            request,
            "Seu usuário não possui matriz e loja operacional vinculadas.",
        )
        return redirect("pdv:inicio")

    if sessao:
        messages.info(request, "Já existe uma sessão de caixa aberta nesta loja.")
        return redirect("pdv:inicio")

    caixa = get_object_or_404(
        Caixa,
        pk=request.POST.get("caixa"),
        matriz=matriz,
        loja=loja,
        status=StatusCaixa.ATIVO,
    )

    valor_texto = (request.POST.get("valor_abertura") or "0").strip()
    valor_texto = valor_texto.replace(".", "").replace(",", ".")

    try:
        valor_abertura = Decimal(valor_texto)
    except Exception:
        messages.error(request, "Informe um valor de abertura válido.")
        return redirect("pdv:abrir_caixa")

    if valor_abertura < 0:
        messages.error(request, "O valor de abertura não pode ser negativo.")
        return redirect("pdv:abrir_caixa")

    observacao = (request.POST.get("observacao_abertura") or "").strip()

    try:
        with transaction.atomic():
            sessao = SessaoCaixa(
                caixa=caixa,
                operador_abertura=request.user,
                valor_abertura=valor_abertura,
                observacao_abertura=observacao,
            )
            sessao.full_clean()
            sessao.save()

            MovimentacaoCaixa.objects.create(
                sessao_caixa=sessao,
                tipo=TipoMovimentacaoCaixa.ABERTURA,
                valor=valor_abertura,
                operador=request.user,
                descricao="Abertura da sessão de caixa.",
            )
    except (ValidationError, IntegrityError) as exc:
        messages.error(
            request,
            "Não foi possível abrir o caixa. Verifique se ele já possui uma sessão aberta.",
        )
        return redirect("pdv:abrir_caixa")

    messages.success(
        request,
        f"{caixa.nome} aberto com sucesso.",
    )
    return redirect("pdv:inicio")

@login_required
def inicio(request):
    venda, matriz, loja, sessao = _obter_venda_atual(request, criar=False)
    contexto = {
        "venda": venda,
        "loja": loja,
        "sessao_caixa": sessao,
        "caixa_aberto": bool(sessao),
    }
    return render(request, "pdv/inicio.html", contexto)


@login_required
@require_GET
def estado_venda(request):
    venda, _, _, _ = _obter_venda_atual(request, criar=False)
    return JsonResponse({"ok": True, "venda": _serializar_venda(venda)})


@login_required
@require_GET
def buscar_produtos(request):
    matriz = getattr(request.user, "matriz", None)
    termo = (request.GET.get("q") or "").strip()

    if matriz is None:
        return JsonResponse(
            {"ok": False, "erro": "O usuário não possui matriz vinculada."},
            status=400,
        )

    if len(termo) < 2:
        return JsonResponse({"ok": True, "produtos": []})

    produto_exato = get_produto_por_codigo(matriz=matriz, codigo=termo)
    queryset = get_produtos(
        matriz=matriz,
        busca=termo,
        somente_ativos=True,
    )[:12]

    produtos = list(queryset)
    if produto_exato and produto_exato not in produtos:
        produtos.insert(0, produto_exato)

    dados = [
        {
            "id": produto.pk,
            "nome": produto.nome,
            "codigo": produto.codigo_interno,
            "sku": produto.sku,
            "gtin": produto.gtin,
            "preco": str(produto.preco_venda),
            "controla_estoque": produto.controla_estoque,
        }
        for produto in produtos[:12]
    ]
    return JsonResponse({"ok": True, "produtos": dados})


@login_required
@require_POST
@transaction.atomic
def adicionar_item(request):
    venda, matriz, _, sessao = _obter_venda_atual(request, criar=True)
    if not sessao:
        return JsonResponse(
            {"ok": False, "erro": "Não existe sessão de caixa aberta para esta loja."},
            status=409,
        )

    try:
        produto = get_produto(
            matriz=matriz,
            produto_id=request.POST.get("produto_id"),
        )
        adicionar_item_venda(
            venda=venda,
            produto=produto,
            quantidade=request.POST.get("quantidade") or Decimal("1.000"),
            usuario=request.user,
            request=request,
        )
    except (Produto.DoesNotExist, ValueError, ValidationError) as exc:
        mensagem = (
            "Produto não encontrado."
            if isinstance(exc, Produto.DoesNotExist)
            else _erro_validacao(exc)
        )
        return JsonResponse({"ok": False, "erro": mensagem}, status=400)

    return JsonResponse({"ok": True, "venda": _serializar_venda(venda)})


@login_required
@require_POST
@transaction.atomic
def alterar_item(request, item_id):
    venda, _, _, _ = _obter_venda_atual(request, criar=False)
    if venda is None:
        return JsonResponse({"ok": False, "erro": "Venda não encontrada."}, status=404)

    item = get_object_or_404(
        ItemVenda.objects.select_related("venda", "produto"),
        pk=item_id,
        venda=venda,
        cancelado=False,
    )

    try:
        alterar_item_venda(
            item=item,
            quantidade=request.POST.get("quantidade"),
            desconto=request.POST.get("desconto"),
            usuario=request.user,
            request=request,
        )
    except ValidationError as exc:
        return JsonResponse(
            {"ok": False, "erro": _erro_validacao(exc)},
            status=400,
        )

    return JsonResponse({"ok": True, "venda": _serializar_venda(venda)})


@login_required
@require_POST
@transaction.atomic
def cancelar_item(request, item_id):
    venda, _, _, _ = _obter_venda_atual(request, criar=False)
    if venda is None:
        return JsonResponse({"ok": False, "erro": "Venda não encontrada."}, status=404)

    item = get_object_or_404(
        ItemVenda.objects.select_related("venda", "produto"),
        pk=item_id,
        venda=venda,
        cancelado=False,
    )

    try:
        cancelar_item_venda(
            item=item,
            motivo=request.POST.get("motivo") or "Removido na frente de caixa.",
            usuario=request.user,
            request=request,
        )
    except ValidationError as exc:
        return JsonResponse(
            {"ok": False, "erro": _erro_validacao(exc)},
            status=400,
        )

    return JsonResponse({"ok": True, "venda": _serializar_venda(venda)})
