from vouchers.models import UsoVoucher, Voucher
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db import transaction
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import JsonResponse
import json
from django.contrib.auth import get_user_model
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
    FormaPagamento,
    ItemVenda,
    MovimentacaoCaixa,
    PagamentoVenda,
    SessaoCaixa,
    Venda,
)
from pdv.services.cliente_consumidor import obter_ou_criar_cliente_consumidor
from clientes.models import Cliente
from beneficios.selectors import get_resumo_beneficios
from beneficios.services.estrategia import calcular_desconto_voucher
from cashback.services.compra import calcular_cashback
from core.services import garantir_configuracao_sistema
from pdv.services.vendas import (
    adicionar_item_venda,
    alterar_item_venda,
    cancelar_item_venda,
    finalizar_venda,
)
from pdv.services.vendas.cancelamento import cancelar_venda
from pdv.services.vendas.caixa import abrir_sessao_caixa
from accounts.decorators import require_permission
from accounts.services import usuario_tem_permissao
from pdv.constants import (
    PERMISSAO_PDV_ABRIR_CAIXA,
    PERMISSAO_PDV_AUTORIZAR_DESCONTO,
    PERMISSAO_PDV_CANCELAR_VENDA,
    PERMISSAO_PDV_FECHAR_CAIXA,
    PERMISSAO_PDV_OPERAR,
    PERMISSAO_PDV_VISUALIZAR,
)
# PDV-ACL-01 - PROTECOES FINAS
from pdv.services.vendas.beneficios import resolver_beneficio_da_venda
from pdv.services.vendas.fechamento import (
    fechar_venda_web,
    serializar_formas_pagamento,
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



# PDV-04E.1.1 - FORMATACAO MONETARIA DO FECHAMENTO
def _formatar_valor_monetario_br(valor):
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "#").replace(".", ",").replace("#", ".")
    return f"R$ {texto}"


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
            operador_abertura=request.user,
            status=StatusSessaoCaixa.ABERTA,
        )
        .order_by("aberta_em", "id")
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


def _serializar_usuario(usuario):
    if usuario is None:
        return None
    nome = usuario.get_full_name().strip() or usuario.username
    return {
        "id": usuario.pk,
        "nome": nome,
        "username": usuario.username,
    }


def _serializar_cliente(cliente):
    if cliente is None:
        return None
    return {
        "id": cliente.pk,
        "nome": cliente.nome,
        "cpf": cliente.cpf,
        "telefone": cliente.telefone or "",
        "email": cliente.email or "",
    }



def _serializar_beneficios(venda):
    if venda is None or venda.cliente is None:
        return {
            "cashback_disponivel": "0.00",
            "voucher_recomendado": None,
            "desconto_recomendado": "0.00",
            "cashback_previsto": "0.00",
            "percentual_cashback": "0.00",
        }

    resumo = get_resumo_beneficios(
        matriz=venda.matriz,
        cliente=venda.cliente,
    )
    configuracao = garantir_configuracao_sistema(matriz=venda.matriz)
    valor_compra = Decimal(venda.total or 0)

    vouchers_cliente = [
        voucher
        for voucher in resumo.get("vouchers_disponiveis", [])
        if voucher.cliente_id == venda.cliente_id
    ]

    voucher = None
    desconto = Decimal("0.00")
    if valor_compra > 0:
        for candidato in vouchers_cliente:
            desconto_candidato = calcular_desconto_voucher(
                voucher=candidato,
                valor_compra=valor_compra,
            )
            if voucher is None or desconto_candidato > desconto:
                voucher = candidato
                desconto = desconto_candidato

    cashback_previsto = calcular_cashback(
        valor_compra=valor_compra,
        percentual=configuracao.percentual_cashback,
    )

    voucher_serializado = None
    if voucher is not None:
        voucher_serializado = {
            "id": voucher.pk,
            "codigo": voucher.codigo,
            "nome": voucher.nome,
            "tipo": voucher.tipo,
            "valor": str(voucher.valor) if voucher.valor is not None else None,
            "percentual": str(voucher.percentual) if voucher.percentual is not None else None,
            "data_fim": voucher.data_fim.isoformat(),
        }

    return {
        "cashback_disponivel": str(resumo["cashback_disponivel"]),
        "voucher_recomendado": voucher_serializado,
        "desconto_recomendado": str(desconto),
        "cashback_previsto": str(cashback_previsto),
        "percentual_cashback": str(configuracao.percentual_cashback),
    }


def _serializar_venda(venda):
    if venda is None:
        return {
            "id": None,
            "status": None,
            "status_display": "Nova venda",
            "finalizada_em": None,
            "quantidade_itens": "0.000",
            "subtotal": "0.00",
            "desconto": "0.00",
            "acrescimo": "0.00",
            "total": "0.00",
            "cliente": None,
            "vendedor": None,
            "beneficios": _serializar_beneficios(None),
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
        "status": venda.status,
        "status_display": venda.get_status_display(),
        "finalizada_em": (
            venda.finalizada_em.isoformat()
            if venda.finalizada_em is not None
            else None
        ),
        "quantidade_itens": str(venda.quantidade_itens),
        "subtotal": str(venda.subtotal),
        "desconto": str(venda.desconto),
        "acrescimo": str(venda.acrescimo),
        "total": str(venda.total),
        "cliente": _serializar_cliente(venda.cliente),
        "vendedor": _serializar_usuario(venda.vendedor),
        "beneficios": _serializar_beneficios(venda),
        "itens": [_serializar_item(item) for item in itens],
    }


@login_required
@require_GET
@require_permission(PERMISSAO_PDV_ABRIR_CAIXA)
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
@require_permission(PERMISSAO_PDV_ABRIR_CAIXA)
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
        sessao = abrir_sessao_caixa(
            caixa=caixa,
            operador=request.user,
            valor_abertura=valor_abertura,
            observacao=observacao,
        )
    except (ValidationError, IntegrityError) as exc:
        mensagem = (
            exc.messages[0]
            if isinstance(exc, ValidationError)
            and getattr(exc, "messages", None)
            else "Nao foi possivel abrir o caixa. Verifique as sessoes abertas."
        )
        messages.error(request, mensagem)
        return redirect("pdv:abrir_caixa")

    messages.success(
        request,
        f"{caixa.nome} aberto com sucesso.",
    )
    return redirect("pdv:inicio")

@login_required
@require_permission(PERMISSAO_PDV_VISUALIZAR)
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
@require_permission(PERMISSAO_PDV_VISUALIZAR)
def estado_venda(request):
    venda, _, _, _ = _obter_venda_atual(request, criar=False)
    return JsonResponse({"ok": True, "venda": _serializar_venda(venda)})


@login_required
@require_GET
@require_permission(PERMISSAO_PDV_OPERAR)
def buscar_clientes(request):
    matriz = getattr(request.user, "matriz", None)
    termo = (request.GET.get("q") or "").strip()

    if matriz is None:
        return JsonResponse(
            {"ok": False, "erro": "O usuário não possui matriz vinculada."},
            status=400,
        )

    if len(termo) < 2:
        return JsonResponse({"ok": True, "clientes": []})

    somente_numeros = "".join(caractere for caractere in termo if caractere.isdigit())
    filtros = Q(nome__icontains=termo) | Q(email__icontains=termo)
    if somente_numeros:
        filtros |= Q(cpf_normalizado__icontains=somente_numeros)
        filtros |= Q(telefone_normalizado__icontains=somente_numeros)
        filtros |= Q(cpf__icontains=termo)
        filtros |= Q(telefone__icontains=termo)

    clientes = (
        Cliente.objects.filter(matriz=matriz, ativo=True)
        .filter(filtros)
        .order_by("nome")[:12]
    )
    return JsonResponse({
        "ok": True,
        "clientes": [_serializar_cliente(cliente) for cliente in clientes],
    })


@login_required
@require_POST
@transaction.atomic
@require_permission(PERMISSAO_PDV_OPERAR)
def selecionar_cliente(request):
    venda, matriz, _, sessao = _obter_venda_atual(request, criar=True)
    if not matriz or not sessao or venda is None:
        return JsonResponse(
            {"ok": False, "erro": "Abra o caixa antes de selecionar o cliente."},
            status=400,
        )

    cliente = get_object_or_404(
        Cliente,
        pk=request.POST.get("cliente_id"),
        matriz=matriz,
        ativo=True,
    )
    venda.cliente = cliente
    venda.full_clean()
    venda.save(update_fields=["cliente", "atualizada_em"])
    return JsonResponse({"ok": True, "venda": _serializar_venda(venda)})


@login_required
@require_GET
@require_permission(PERMISSAO_PDV_OPERAR)
def buscar_vendedores(request):
    matriz = getattr(request.user, "matriz", None)
    _, loja, _ = _contexto_operacional(request)
    termo = (request.GET.get("q") or "").strip()

    if matriz is None or loja is None:
        return JsonResponse(
            {"ok": False, "erro": "O usuário não possui contexto operacional."},
            status=400,
        )

    usuarios = get_user_model().objects.filter(
        matriz=matriz,
        ativo=True,
        is_active=True,
        lojas=loja,
    )
    if termo:
        usuarios = usuarios.filter(
            Q(username__icontains=termo)
            | Q(first_name__icontains=termo)
            | Q(last_name__icontains=termo)
        )

    vendedores = usuarios.distinct().order_by("first_name", "username")[:30]
    return JsonResponse({
        "ok": True,
        "vendedores": [_serializar_usuario(usuario) for usuario in vendedores],
    })


@login_required
@require_POST
@transaction.atomic
@require_permission(PERMISSAO_PDV_OPERAR)
def selecionar_vendedor(request):
    venda, matriz, loja, sessao = _obter_venda_atual(request, criar=True)
    if not matriz or not loja or not sessao or venda is None:
        return JsonResponse(
            {"ok": False, "erro": "Abra o caixa antes de selecionar o vendedor."},
            status=400,
        )

    vendedor = get_object_or_404(
        get_user_model(),
        pk=request.POST.get("vendedor_id"),
        matriz=matriz,
        ativo=True,
        is_active=True,
        lojas=loja,
    )
    venda.vendedor = vendedor
    venda.full_clean()
    venda.save(update_fields=["vendedor", "atualizada_em"])
    return JsonResponse({"ok": True, "venda": _serializar_venda(venda)})


@login_required
@require_GET
@require_permission(PERMISSAO_PDV_OPERAR)
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
@require_permission(PERMISSAO_PDV_OPERAR)
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
@require_permission(PERMISSAO_PDV_OPERAR)
def alterar_item(request, item_id):
    desconto_informado = request.POST.get("desconto")
    if (
        desconto_informado not in (None, "", "0", "0.00", "0,00")
        and not usuario_tem_permissao(
            request.user,
            PERMISSAO_PDV_AUTORIZAR_DESCONTO,
        )
    ):
        return JsonResponse(
            {
                "ok": False,
                "erro": "Usuario sem permissao para autorizar desconto.",
            },
            status=403,
        )

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
@require_permission(PERMISSAO_PDV_OPERAR)
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


@login_required
@require_GET
@require_permission(PERMISSAO_PDV_OPERAR)
def opcoes_fechamento(request):
    venda, matriz, _, sessao = _obter_venda_atual(request, criar=False)
    if sessao is None or matriz is None:
        return JsonResponse({"ok": False, "erro": "Abra o caixa antes de fechar a venda."}, status=409)
    if venda is None:
        return JsonResponse({"ok": False, "erro": "Venda atual não encontrada."}, status=404)
    return JsonResponse({
        "ok": True,
        "venda": _serializar_venda(venda),
        "formas_pagamento": serializar_formas_pagamento(matriz=matriz),
    })


@login_required
@require_POST
@require_permission(PERMISSAO_PDV_OPERAR)
def finalizar_venda_web(request):
    venda, _, _, sessao = _obter_venda_atual(request, criar=False)
    if sessao is None:
        return JsonResponse({"ok": False, "erro": "Abra o caixa antes de finalizar."}, status=409)
    if venda is None:
        return JsonResponse({"ok": False, "erro": "Venda atual não encontrada."}, status=404)
    try:
        dados = json.loads(request.body.decode("utf-8") or "{}")
        venda_finalizada = fechar_venda_web(
            venda=venda,
            usuario=request.user,
            pagamentos=dados.get("pagamentos") or [],
            tipo_emissao=dados.get("tipo_emissao") or "nao_fiscal",
            uf_destino=dados.get("uf_destino") or "",
            tipo_beneficio=dados.get("tipo_beneficio") or "nenhum",
            valor_cashback=dados.get("valor_cashback") or "0",
            codigo_voucher=dados.get("codigo_voucher") or "",
            request=request,
        )
    except (json.JSONDecodeError, TypeError, ValueError, ValidationError) as exc:
        mensagem = "Dados inválidos." if isinstance(exc, json.JSONDecodeError) else _erro_validacao(exc)
        return JsonResponse({"ok": False, "erro": mensagem}, status=400)
    return JsonResponse({
        "ok": True,
        "mensagem": "Venda finalizada com sucesso.",
        "venda": _serializar_venda(venda_finalizada),
    })


# PDV-04.2 V5 - VOUCHER E CANCELAMENTO
@login_required
@require_POST
@require_permission(PERMISSAO_PDV_OPERAR)
def validar_voucher_venda_web(request):
    venda, _, _, _ = _obter_venda_atual(request, criar=False)
    if venda is None:
        return JsonResponse(
            {"ok": False, "erro": "Nenhuma venda em andamento."},
            status=404,
        )

    codigo = (request.POST.get("codigo") or "").strip().upper()
    if not codigo:
        return JsonResponse(
            {"ok": False, "erro": "Informe o codigo do voucher."},
            status=400,
        )

    try:
        beneficio = resolver_beneficio_da_venda(
            matriz=venda.matriz,
            loja=venda.loja,
            cliente=venda.cliente,
            valor_compra=venda.total,
            tipo_beneficio="voucher",
            valor_cashback=Decimal("0.00"),
            codigo_voucher=codigo,
        )
    except ValidationError as exc:
        erro = _erro_validacao(exc)
        status = 404 if "nao encontrado" in erro.lower() else 400
        return JsonResponse({"ok": False, "erro": erro}, status=status)

    voucher = beneficio.voucher
    return JsonResponse({
        "ok": True,
        "voucher": {
            "id": voucher.pk,
            "codigo": voucher.codigo,
            "nome": voucher.nome,
            "cliente": voucher.cliente.nome if voucher.cliente_id else None,
            "desconto": str(beneficio.valor),
            "data_fim": voucher.data_fim.isoformat(),
        },
    })


@login_required
@require_POST
@require_permission(PERMISSAO_PDV_CANCELAR_VENDA)
def cancelar_venda_web(request):
    venda, _, _, _ = _obter_venda_atual(request, criar=False)

    if venda is None:
        return JsonResponse({
            "ok": True,
            "mensagem": "Nao havia venda em andamento.",
        })

    try:
        cancelar_venda(
            venda=venda,
            usuario=request.user,
            request=request,
            motivo=request.POST.get("motivo") or "Venda cancelada na frente de caixa.",
        )
    except ValidationError as exc:
        return JsonResponse(
            {"ok": False, "erro": _erro_validacao(exc)},
            status=400,
        )

    return JsonResponse({
        "ok": True,
        "mensagem": "Venda cancelada. O caixa esta pronto para uma nova venda.",
    })

# PDV-04C.1 - VIEWS DE FECHAMENTO DE CAIXA
def _pdv04c1_sessao_aberta_do_usuario(request):
    from pdv.choices import StatusSessaoCaixa
    from pdv.models import SessaoCaixa

    matriz = getattr(request.user, "matriz", None)
    lojas = getattr(request.user, "lojas", None)

    queryset = (
        SessaoCaixa.objects
        .select_related("caixa", "caixa__loja")
        .filter(
            operador_abertura=request.user,
            status=StatusSessaoCaixa.ABERTA,
        )
    )

    if matriz is not None:
        queryset = queryset.filter(caixa__matriz=matriz)

    if lojas is not None:
        queryset = queryset.filter(caixa__loja__in=lojas.all())

    return queryset.order_by("aberta_em", "id").first()


# CFG-PDV-01 - AUTORIZACAO PELO MECANISMO CENTRAL
def fechar_caixa(request):
    from django.contrib import messages
    from django.core.exceptions import ValidationError
    from django.http import HttpResponseForbidden
    from django.shortcuts import redirect, render
    from pdv.constants import PERMISSAO_PDV_FECHAR_CAIXA
    from pdv.services.vendas.caixa import calcular_saldo_sessao_caixa

    from accounts.services import usuario_tem_permissao

    if not usuario_tem_permissao(
        request.user,
        PERMISSAO_PDV_FECHAR_CAIXA,
    ):
        return HttpResponseForbidden("Usuario sem permissao para fechar o caixa.")

    try:
        sessao = _pdv04c1_sessao_aberta_do_usuario(request)
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
        return redirect("pdv:inicio")

    if sessao is None:
        messages.warning(request, "Nao existe caixa aberto para fechamento.")
        return redirect("pdv:inicio")

    return render(
        request,
        "pdv/fechar_caixa.html",
        {
            "sessao": sessao,
            "valor_calculado": calcular_saldo_sessao_caixa(sessao=sessao),
            "valor_fechamento_inicial": (
                request.session.pop("pdv_valor_fechamento_informado", None)
                or _formatar_valor_monetario_br(
                    calcular_saldo_sessao_caixa(sessao=sessao)
                )
            ),
            "observacao_fechamento_inicial": request.session.pop(
                "pdv_observacao_fechamento",
                "",
            ),
        },
    )


def confirmar_fechamento_caixa(request):
    from decimal import Decimal, InvalidOperation
    from django.contrib import messages
    from django.core.exceptions import ValidationError
    from django.http import HttpResponseForbidden, HttpResponseNotAllowed
    from django.shortcuts import redirect
    from pdv.constants import PERMISSAO_PDV_FECHAR_CAIXA
    from pdv.services.vendas.caixa import fechar_sessao_caixa

    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    from accounts.services import usuario_tem_permissao

    if not usuario_tem_permissao(
        request.user,
        PERMISSAO_PDV_FECHAR_CAIXA,
    ):
        return HttpResponseForbidden("Usuario sem permissao para fechar o caixa.")

    try:
        sessao = _pdv04c1_sessao_aberta_do_usuario(request)
        if sessao is None:
            raise ValidationError("Nao existe caixa aberto para fechamento.")

        texto = (request.POST.get("valor_fechamento") or "").strip()
        observacao = (request.POST.get("observacao_fechamento") or "").strip()
        request.session["pdv_valor_fechamento_informado"] = texto
        request.session["pdv_observacao_fechamento"] = observacao

        if not texto:
            raise InvalidOperation

        normalizado = texto.replace("R$", "").replace(" ", "")
        if "," in normalizado:
            normalizado = normalizado.replace(".", "").replace(",", ".")
        valor = Decimal(normalizado)

        resultado = fechar_sessao_caixa(
            sessao_id=sessao.pk,
            operador=request.user,
            valor_informado=valor,
            observacao=observacao,
        )
    except (InvalidOperation, ValueError):
        messages.error(request, "Informe um valor de fechamento valido.")
        return redirect("pdv:fechar_caixa")
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
        return redirect("pdv:fechar_caixa")

    request.session.pop("pdv_valor_fechamento_informado", None)
    request.session.pop("pdv_observacao_fechamento", None)

    diferenca = resultado.diferenca_fechamento
    if diferenca == Decimal("0.00"):
        resumo = "Fechamento conferido, sem diferenca."
    elif diferenca > Decimal("0.00"):
        resumo = f"Sobra de R$ {diferenca:.2f}."
    else:
        resumo = f"Falta de R$ {abs(diferenca):.2f}."

    messages.success(
        request,
        (
            f"Caixa {resultado.caixa.nome} fechado com sucesso. "
            f"Calculado: R$ {resultado.valor_fechamento_calculado:.2f}. "
            f"Informado: R$ {resultado.valor_fechamento_informado:.2f}. "
            f"{resumo}"
        ),
    )
    return redirect("pdv:inicio")

# PDV-04E.2 - HISTORICO DE FECHAMENTOS
@login_required
@require_GET
@require_permission(PERMISSAO_PDV_FECHAR_CAIXA)
def historico_fechamentos(request):
    from datetime import datetime

    from django.core.paginator import Paginator
    from django.db.models import Count, Sum
    from django.db.models.functions import Coalesce
    from django.utils import timezone

    matriz = getattr(request.user, "matriz", None)
    lojas_relacao = getattr(request.user, "lojas", None)

    if matriz is None or lojas_relacao is None:
        messages.error(
            request,
            "Seu usuario nao possui contexto operacional para consultar caixas.",
        )
        return redirect("pdv:inicio")

    lojas = lojas_relacao.filter(matriz=matriz).order_by("nome")
    sessoes = (
        SessaoCaixa.objects
        .select_related(
            "caixa",
            "caixa__loja",
            "operador_abertura",
            "operador_fechamento",
        )
        .filter(
            caixa__matriz=matriz,
            caixa__loja__in=lojas,
        )
        .order_by("-aberta_em")
    )

    data_inicio = (request.GET.get("data_inicio") or "").strip()
    data_fim = (request.GET.get("data_fim") or "").strip()
    caixa_id = (request.GET.get("caixa") or "").strip()
    operador_id = (request.GET.get("operador") or "").strip()
    status = (request.GET.get("status") or "").strip()

    if data_inicio:
        try:
            inicio_data = datetime.strptime(data_inicio, "%Y-%m-%d").date()
            sessoes = sessoes.filter(aberta_em__date__gte=inicio_data)
        except ValueError:
            messages.warning(request, "Data inicial invalida.")

    if data_fim:
        try:
            fim_data = datetime.strptime(data_fim, "%Y-%m-%d").date()
            sessoes = sessoes.filter(aberta_em__date__lte=fim_data)
        except ValueError:
            messages.warning(request, "Data final invalida.")

    if caixa_id.isdigit():
        sessoes = sessoes.filter(caixa_id=int(caixa_id))

    if operador_id.isdigit():
        sessoes = sessoes.filter(
            Q(operador_abertura_id=int(operador_id))
            | Q(operador_fechamento_id=int(operador_id))
        )

    status_validos = {
        escolha[0]
        for escolha in StatusSessaoCaixa.choices
    }
    if status in status_validos:
        sessoes = sessoes.filter(status=status)

    totais = sessoes.aggregate(
        total_sessoes=Count("id"),
        total_abertura=Coalesce(
            Sum("valor_abertura"),
            Decimal("0.00"),
        ),
        total_calculado=Coalesce(
            Sum("valor_fechamento_calculado"),
            Decimal("0.00"),
        ),
        total_informado=Coalesce(
            Sum("valor_fechamento_informado"),
            Decimal("0.00"),
        ),
        total_diferenca=Coalesce(
            Sum("diferenca_fechamento"),
            Decimal("0.00"),
        ),
    )

    caixas = (
        Caixa.objects
        .filter(
            matriz=matriz,
            loja__in=lojas,
        )
        .select_related("loja")
        .order_by("loja__nome", "nome")
    )

    User = get_user_model()
    operadores = (
        User.objects
        .filter(
            matriz=matriz,
            lojas__in=lojas,
            ativo=True,
            is_active=True,
        )
        .distinct()
        .order_by("first_name", "username")
    )

    paginator = Paginator(sessoes, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    query_params = request.GET.copy()
    query_params.pop("page", None)

    return render(
        request,
        "pdv/historico_fechamentos.html",
        {
            "page_obj": page_obj,
            "sessoes": page_obj.object_list,
            "totais": totais,
            "caixas": caixas,
            "operadores": operadores,
            "status_opcoes": StatusSessaoCaixa.choices,
            "filtros": {
                "data_inicio": data_inicio,
                "data_fim": data_fim,
                "caixa": caixa_id,
                "operador": operador_id,
                "status": status,
            },
            "query_string": query_params.urlencode(),
        },
    )

# PDV-04E.3 - HISTORICO DE VENDAS
@login_required
@require_GET
@require_permission(PERMISSAO_PDV_VISUALIZAR)
def historico_vendas(request):
    from datetime import datetime

    from django.core.paginator import Paginator
    from django.db.models import Count, Sum
    from django.db.models.functions import Coalesce

    matriz = getattr(request.user, "matriz", None)
    lojas_relacao = getattr(request.user, "lojas", None)

    if matriz is None or lojas_relacao is None:
        messages.error(
            request,
            "Seu usuario nao possui contexto operacional para consultar vendas.",
        )
        return redirect("pdv:inicio")

    lojas = lojas_relacao.filter(matriz=matriz).order_by("nome")

    vendas = (
        Venda.objects
        .select_related(
            "loja",
            "cliente",
            "operador",
            "vendedor",
            "sessao_caixa",
            "sessao_caixa__caixa",
        )
        .prefetch_related(
            "pagamentos__forma_pagamento",
        )
        .filter(
            matriz=matriz,
            loja__in=lojas,
            status__in=[
                StatusOperacaoVenda.FINALIZADA,
                StatusOperacaoVenda.CANCELADA,
            ],
        )
        .order_by("-criada_em")
    )

    data_inicio = (request.GET.get("data_inicio") or "").strip()
    data_fim = (request.GET.get("data_fim") or "").strip()
    numero = (request.GET.get("numero") or "").strip()
    cliente = (request.GET.get("cliente") or "").strip()
    vendedor_id = (request.GET.get("vendedor") or "").strip()
    operador_id = (request.GET.get("operador") or "").strip()
    status = (request.GET.get("status") or "").strip()
    forma_pagamento_id = (
        request.GET.get("forma_pagamento") or ""
    ).strip()
    caixa_id = (request.GET.get("caixa") or "").strip()
    loja_id = (request.GET.get("loja") or "").strip()

    if data_inicio:
        try:
            inicio_data = datetime.strptime(
                data_inicio,
                "%Y-%m-%d",
            ).date()
            vendas = vendas.filter(criada_em__date__gte=inicio_data)
        except ValueError:
            messages.warning(request, "Data inicial invalida.")

    if data_fim:
        try:
            fim_data = datetime.strptime(
                data_fim,
                "%Y-%m-%d",
            ).date()
            vendas = vendas.filter(criada_em__date__lte=fim_data)
        except ValueError:
            messages.warning(request, "Data final invalida.")

    if numero.isdigit():
        vendas = vendas.filter(numero=int(numero))

    if cliente:
        vendas = vendas.filter(
            Q(cliente__nome__icontains=cliente)
            | Q(cliente__cpf__icontains=cliente)
            | Q(cliente__telefone__icontains=cliente)
            | Q(cliente__email__icontains=cliente)
        )

    if vendedor_id.isdigit():
        vendas = vendas.filter(vendedor_id=int(vendedor_id))

    if operador_id.isdigit():
        vendas = vendas.filter(operador_id=int(operador_id))

    status_validos = {
        StatusOperacaoVenda.FINALIZADA,
        StatusOperacaoVenda.CANCELADA,
    }
    if status in status_validos:
        vendas = vendas.filter(status=status)

    if forma_pagamento_id.isdigit():
        vendas = vendas.filter(
            pagamentos__forma_pagamento_id=int(
                forma_pagamento_id
            )
        )

    if caixa_id.isdigit():
        vendas = vendas.filter(
            sessao_caixa__caixa_id=int(caixa_id)
        )

    if loja_id.isdigit():
        vendas = vendas.filter(loja_id=int(loja_id))

    vendas = vendas.distinct()

    totais = vendas.aggregate(
        total_vendas=Count("id", distinct=True),
        valor_total=Coalesce(
            Sum("total"),
            Decimal("0.00"),
        ),
        total_descontos=Coalesce(
            Sum("desconto"),
            Decimal("0.00"),
        ),
        total_acrescimos=Coalesce(
            Sum("acrescimo"),
            Decimal("0.00"),
        ),
    )

    User = get_user_model()

    vendedores = (
        User.objects
        .filter(
            matriz=matriz,
            lojas__in=lojas,
            ativo=True,
            is_active=True,
        )
        .distinct()
        .order_by("first_name", "username")
    )

    operadores = vendedores

    formas_pagamento = (
        FormaPagamento.objects
        .filter(
            matriz=matriz,
            pagamentos_venda__venda__loja__in=lojas,
        )
        .distinct()
        .order_by("nome")
    )

    caixas = (
        Caixa.objects
        .filter(
            matriz=matriz,
            loja__in=lojas,
        )
        .select_related("loja")
        .order_by("loja__nome", "nome")
    )

    paginator = Paginator(vendas, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    query_params = request.GET.copy()
    query_params.pop("page", None)

    return render(
        request,
        "pdv/historico_vendas.html",
        {
            "page_obj": page_obj,
            "vendas": page_obj.object_list,
            "totais": totais,
            "lojas": lojas,
            "vendedores": vendedores,
            "operadores": operadores,
            "formas_pagamento": formas_pagamento,
            "caixas": caixas,
            "status_opcoes": [
                (
                    StatusOperacaoVenda.FINALIZADA,
                    "Finalizada",
                ),
                (
                    StatusOperacaoVenda.CANCELADA,
                    "Cancelada",
                ),
            ],
            "filtros": {
                "data_inicio": data_inicio,
                "data_fim": data_fim,
                "numero": numero,
                "cliente": cliente,
                "vendedor": vendedor_id,
                "operador": operador_id,
                "status": status,
                "forma_pagamento": forma_pagamento_id,
                "caixa": caixa_id,
                "loja": loja_id,
            },
            "query_string": query_params.urlencode(),
        },
    )


@login_required
@require_GET
@require_permission(PERMISSAO_PDV_VISUALIZAR)
def detalhe_venda(request, venda_uuid):
    from django.db.models import Sum
    from django.db.models.functions import Coalesce

    matriz = getattr(request.user, "matriz", None)
    lojas_relacao = getattr(request.user, "lojas", None)

    if matriz is None or lojas_relacao is None:
        messages.error(
            request,
            "Seu usuario nao possui contexto operacional para consultar vendas.",
        )
        return redirect("pdv:inicio")

    lojas = lojas_relacao.filter(matriz=matriz)

    venda = get_object_or_404(
        Venda.objects
        .select_related(
            "loja",
            "cliente",
            "operador",
            "vendedor",
            "sessao_caixa",
            "sessao_caixa__caixa",
        )
        .prefetch_related(
            "itens__produto",
            "itens__cancelado_por",
            "pagamentos__forma_pagamento",
            "pagamentos__autorizado_por",
        ),
        uuid=venda_uuid,
        matriz=matriz,
        loja__in=lojas,
        status__in=[
            StatusOperacaoVenda.FINALIZADA,
            StatusOperacaoVenda.CANCELADA,
        ],
    )

    itens = venda.itens.all().order_by("sequencia")
    pagamentos = (
        venda.pagamentos
        .select_related(
            "forma_pagamento",
            "autorizado_por",
        )
        .order_by("criado_em")
    )

    resumo_pagamentos = pagamentos.aggregate(
        total_pago=Coalesce(
            Sum("valor"),
            Decimal("0.00"),
        ),
        total_troco=Coalesce(
            Sum("troco"),
            Decimal("0.00"),
        ),
    )

    return render(
        request,
        "pdv/detalhe_venda.html",
        {
            "venda": venda,
            "itens": itens,
            "pagamentos": pagamentos,
            "resumo_pagamentos": resumo_pagamentos,
        },
    )

# PDV-04F.2 - CUPOM DE VENDA NAO FISCAL 80 MM
@login_required
@require_GET
@require_permission(PERMISSAO_PDV_VISUALIZAR)
def cupom_venda_nao_fiscal(request, venda_uuid):
    from decimal import Decimal
    from django.shortcuts import get_object_or_404, redirect, render

    matriz = getattr(request.user, "matriz", None)
    lojas_relacao = getattr(request.user, "lojas", None)
    if matriz is None or lojas_relacao is None:
        messages.error(request, "Seu usuario nao possui contexto operacional para imprimir vendas.")
        return redirect("pdv:inicio")

    lojas = lojas_relacao.filter(matriz=matriz)
    venda = get_object_or_404(
        Venda.objects.select_related(
            "matriz", "loja", "cliente", "operador", "vendedor",
            "sessao_caixa", "sessao_caixa__caixa",
        ).prefetch_related("itens__produto", "pagamentos__forma_pagamento"),
        uuid=venda_uuid,
        matriz=matriz,
        loja__in=lojas,
        status__in=[
            StatusOperacaoVenda.FINALIZADA,
            StatusOperacaoVenda.CANCELADA,
        ],
    )

    itens = list(venda.itens.select_related("produto").order_by("sequencia"))
    pagamentos = list(
        venda.pagamentos.select_related("forma_pagamento").order_by("criado_em", "id")
    )
    total_pago = sum((p.valor for p in pagamentos), Decimal("0.00"))
    total_troco = sum((p.troco for p in pagamentos), Decimal("0.00"))

    return render(request, "pdv/cupom_venda_80mm.html", {
        "venda": venda,
        "itens": itens,
        "pagamentos": pagamentos,
        "total_pago": total_pago,
        "total_troco": total_troco,
        "imprimir_automaticamente": request.GET.get("auto") == "1",
        "segunda_via": request.GET.get("via") == "2",
    })
