from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
# F32M4G - ACL COMERCIAL
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from accounts.services import exigir_permissao
from accounts.permissions import PERMISSAO_ATACADO_VISUALIZAR
from .commercial_access import exigir_acesso_comercial, filtrar_orcamentos_autorizados
from empresas.models import Matriz
from .exports import (
    CONTENT_TYPE_PDF,
    CONTENT_TYPE_XLSX,
    exportar_orcamento_pdf,
    exportar_orcamento_xlsx,
    exportar_pedido_pdf,
    exportar_pedido_xlsx,
)
from .models import OrcamentoAtacado, PedidoAtacado

def _matriz_exportacao(request):
    # O acesso comercial nao utiliza o contexto da Central de Configuracoes.
    matriz_autorizada, _lojas = exigir_acesso_comercial(request)
    if request.user.is_superuser:
        matriz_id = (request.GET.get("matriz") or "").strip()
        if not matriz_id or not matriz_id.isdecimal():
            raise Http404("Selecione explicitamente uma matriz.")
        matriz = get_object_or_404(Matriz, pk=int(matriz_id))
        if matriz_autorizada is not None and matriz.pk != matriz_autorizada.pk:
            raise Http404
        return matriz
    if matriz_autorizada is None:
        raise Http404
    return matriz_autorizada

def _download(dados, content_type, filename):
    response = HttpResponse(dados, content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response

@login_required
def orcamento_pdf(request, pk):
    matriz = _matriz_exportacao(request)
    obj = get_object_or_404(filtrar_orcamentos_autorizados(request, OrcamentoAtacado.objects.all()), pk=pk, matriz=matriz)
    return _download(exportar_orcamento_pdf(obj), CONTENT_TYPE_PDF, f"orcamento_atacado_{obj.numero or obj.pk}.pdf")

@login_required
def orcamento_xlsx(request, pk):
    matriz = _matriz_exportacao(request)
    obj = get_object_or_404(filtrar_orcamentos_autorizados(request, OrcamentoAtacado.objects.all()), pk=pk, matriz=matriz)
    return _download(exportar_orcamento_xlsx(obj), CONTENT_TYPE_XLSX, f"orcamento_atacado_{obj.numero or obj.pk}.xlsx")

@login_required
def pedido_pdf(request, pk):
    matriz = _matriz_exportacao(request)
    _matriz, lojas = exigir_acesso_comercial(request)
    pedidos = PedidoAtacado.objects.filter(matriz=matriz)
    if not request.user.is_superuser and request.user.perfil != "master":
        pedidos = pedidos.filter(loja__in=lojas)
    obj = get_object_or_404(pedidos, pk=pk)
    return _download(exportar_pedido_pdf(obj), CONTENT_TYPE_PDF, f"pedido_atacado_{obj.pk}.pdf")

@login_required
def pedido_xlsx(request, pk):
    matriz = _matriz_exportacao(request)
    _matriz, lojas = exigir_acesso_comercial(request)
    pedidos = PedidoAtacado.objects.filter(matriz=matriz)
    if not request.user.is_superuser and request.user.perfil != "master":
        pedidos = pedidos.filter(loja__in=lojas)
    obj = get_object_or_404(pedidos, pk=pk)
    return _download(exportar_pedido_xlsx(obj), CONTENT_TYPE_XLSX, f"pedido_atacado_{obj.pk}.xlsx")


@login_required
def listar_orcamentos(request):
    from django.core.paginator import Paginator
    from django.shortcuts import render
    from django.db.models import Q

    exigir_permissao(request.user, PERMISSAO_ATACADO_VISUALIZAR)
    matriz = None
    matrizes = None
    if request.user.is_superuser:
        matrizes = Matriz.objects.order_by("nome", "pk")
        matriz_id = (request.GET.get("matriz") or "").strip()
        if matriz_id:
            if not matriz_id.isdecimal():
                raise Http404
            matriz = get_object_or_404(Matriz, pk=int(matriz_id))
    else:
        matriz = getattr(request.user, "matriz", None)
        if matriz is None:
            raise PermissionDenied("Usuario sem matriz.")
    contexto = {"escopo": "plataforma" if request.user.is_superuser else "empresa", "matriz": matriz}

    status = request.GET.get("status", "").strip()
    busca = request.GET.get("q", "").strip()[:100]
    validos = {codigo for codigo, _ in OrcamentoAtacado._meta.get_field("status").choices}
    if status not in validos:
        status = ""
    qs = OrcamentoAtacado.objects.none()
    if matriz is not None:
        qs = filtrar_orcamentos_autorizados(
            request, OrcamentoAtacado.objects.all()
        ).select_related("cliente", "loja", "vendedor")
        if status:
            qs = qs.filter(status=status)
        if busca:
            filtros = Q(cliente__nome__icontains=busca)
            if busca.isdigit():
                filtros |= Q(numero=int(busca)) | Q(pk=int(busca))
            qs = qs.filter(filtros)
    pagina = Paginator(qs.order_by("-id"), 20).get_page(request.GET.get("page"))
    return render(request, "atacado/orcamentos_lista.html", {
        "contexto_configuracoes": contexto,
        "matriz_selecionada": matriz,
        "matrizes_plataforma": matrizes,
        "pagina": pagina,
        "status_atual": status,
        "busca": busca,
        "status_opcoes": OrcamentoAtacado._meta.get_field("status").choices,
        "pode_gerar_pedido": __import__("accounts.services", fromlist=["usuario_tem_permissao"]).usuario_tem_permissao(request.user, __import__("accounts.permissions", fromlist=["PERMISSAO_ATACADO_GERAR_PEDIDO"]).PERMISSAO_ATACADO_GERAR_PEDIDO),
    })


# F32M5D - Cadastro inicial de orcamentos de atacado
@login_required
def novo_orcamento(request):
    from django.contrib import messages
    from django.core.exceptions import ValidationError
    from django.shortcuts import render, redirect
    from django.urls import reverse
    from accounts.permissions import PERMISSAO_ATACADO_CRIAR_ORCAMENTO
    from .forms_cadastro import OrcamentoAtacadoCadastroForm, ItemOrcamentoAtacadoCadastroFormSet
    from .cadastro_services import criar_orcamento_atacado

    matriz, lojas = exigir_acesso_comercial(request, PERMISSAO_ATACADO_CRIAR_ORCAMENTO)
    if not lojas.exists():
        raise PermissionDenied("Usuario sem loja autorizada para o atacado.")
    dados = request.POST if request.method == "POST" else None
    form = OrcamentoAtacadoCadastroForm(dados, matriz=matriz, lojas=lojas)
    formset = ItemOrcamentoAtacadoCadastroFormSet(
        dados, prefix="itens", form_kwargs={"matriz": matriz}
    )
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        itens = [(f.cleaned_data["produto"], f.cleaned_data["quantidade"])
                 for f in formset if f.cleaned_data and not f.cleaned_data.get("DELETE")]
        try:
            orc = criar_orcamento_atacado(
                matriz=matriz, loja=form.cleaned_data["loja"],
                cliente=form.cleaned_data["cliente"], vendedor=form.cleaned_data["vendedor"],
                itens=itens, observacoes=form.cleaned_data["observacoes"],
                frete=form.cleaned_data.get("frete"), validade=form.cleaned_data.get("validade"),
                forma_pagamento=form.cleaned_data.get("forma_pagamento"), parcelas=form.cleaned_data["parcelas"],
            )
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, "Orçamento de atacado criado com sucesso.")
            destino = reverse("atacado:orcamentos_lista")
            if request.user.is_superuser:
                destino += "?matriz=" + str(matriz.pk)
            return redirect(destino)
    return render(request, "atacado/orcamento_novo.html", {
        "form": form, "formset": formset, "matriz": matriz,
        "formas_parcelamento": [
            {"id": fp.pk, "maximo": fp.maximo_parcelas if fp.permite_parcelamento else 1}
            for fp in form.fields["forma_pagamento"].queryset
        ],
    })


# F32M5F3D - Pesquisa comercial para orcamentos.
@login_required
def f32m5f3d_busca_comercial(request):
    from django.http import JsonResponse
    from django.db.models import Q
    from accounts.permissions import PERMISSAO_ATACADO_CRIAR_ORCAMENTO
    from clientes.models import Cliente
    from produtos.models import Produto
    from configuracoes.models import ConfiguracaoComercial
    matriz, lojas = exigir_acesso_comercial(request, PERMISSAO_ATACADO_CRIAR_ORCAMENTO)
    if not lojas.exists():
        raise PermissionDenied('Usuario sem loja autorizada.')
    tipo = (request.GET.get('tipo') or '').strip()
    termo = (request.GET.get('q') or '').strip()[:80]
    if len(termo) < 2 or tipo not in ('clientes', 'produtos'):
        return JsonResponse({'resultados': []})
    if tipo == 'clientes':
        qs = Cliente.objects.filter(matriz=matriz, ativo=True).filter(
            Q(nome__icontains=termo) | Q(cpf__icontains=termo) |
            Q(cnpj__icontains=termo) | Q(razao_social__icontains=termo) |
            Q(nome_fantasia__icontains=termo)
        ).order_by('nome', 'pk')[:15]
        return JsonResponse({'resultados': [
            {'id': x.pk, 'texto': x.nome, 'detalhe': x.cnpj or x.cpf or x.razao_social or ''}
            for x in qs
        ]})
    qs = Produto.objects.filter(matriz=matriz).filter(
        Q(nome__icontains=termo) | Q(sku__icontains=termo) |
        Q(codigo_interno__icontains=termo) | Q(gtin__icontains=termo)
    ).order_by('nome', 'pk')[:15]
    cfg = ConfiguracaoComercial.objects.filter(matriz=matriz).first()
    from configuracoes.models import FaixaAtacado
    faixas = [
        {'minimo': str(f.valor_minimo), 'maximo': str(f.valor_maximo) if f.valor_maximo is not None else None, 'percentual': str(f.percentual_desconto)}
        for f in FaixaAtacado.objects.filter(configuracao=cfg).order_by('valor_minimo')
    ] if cfg else []
    return JsonResponse({'resultados': [
        {'id': x.pk, 'texto': x.nome, 'detalhe': x.sku or x.codigo_interno or x.gtin or '',
         'preco': str(x.preco_venda), 'promocional': bool(x.promocional),
         'elegivel': bool(x.atacado_elegivel)} for x in qs
    ], 'politica': {'minimo': str(cfg.pedido_minimo_atacado) if cfg else '0',
                    'promocional_conta': bool(cfg.produto_promocional_conta_para_faixa_atacado) if cfg else False,
                    'faixas': faixas}})


@login_required
def acao_orcamento(request, pk):
    from django.contrib import messages
    from django.core.exceptions import ValidationError
    from django.db import transaction
    from django.shortcuts import redirect
    from django.urls import reverse
    from django.views.decorators.http import require_POST
    from accounts.permissions import PERMISSAO_ATACADO_GERAR_PEDIDO
    from .models import StatusOrcamentoAtacado
    from .services import transicionar_orcamento, aprovar_orcamento_e_gerar_pedido

    if request.method != "POST":
        return HttpResponse(status=405)
    matriz, _lojas = exigir_acesso_comercial(request, PERMISSAO_ATACADO_GERAR_PEDIDO)
    orc = get_object_or_404(
        filtrar_orcamentos_autorizados(
            request, OrcamentoAtacado.objects.all(), PERMISSAO_ATACADO_GERAR_PEDIDO
        ), pk=pk, matriz=matriz
    )
    acao = request.POST.get("acao", "")
    try:
        if acao == "enviar":
            with transaction.atomic():
                atual = OrcamentoAtacado.objects.select_for_update().get(pk=orc.pk)
                transicionar_orcamento(
                    atual, StatusOrcamentoAtacado.ENVIADO,
                    usuario=request.user, observacao="Orçamento marcado como enviado.",
                )
            messages.success(request, "Orçamento marcado como enviado.")
        elif acao == "aprovar":
            pedido = aprovar_orcamento_e_gerar_pedido(orc, usuario=request.user)
            messages.success(request, f"Orçamento aprovado e pedido #{pedido.pk} gerado com sucesso.")
        else:
            raise Http404("Ação inválida.")
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
    destino = reverse("atacado:orcamentos_lista")
    if request.user.is_superuser:
        destino += "?matriz=" + str(matriz.pk)
    return redirect(destino)


# F32M5P12C - consulta de pedidos e cancelamento de propostas ainda nao convertidas.
@login_required
def listar_pedidos_atacado(request):
    from django.shortcuts import render
    from django.core.paginator import Paginator
    from django.db.models import Q
    from .models import StatusPedidoAtacado
    matriz, lojas = exigir_acesso_comercial(request)
    qs = PedidoAtacado.objects.filter(matriz=matriz).select_related(
        "cliente", "loja", "orcamento_origem"
    )
    if not request.user.is_superuser and request.user.perfil != "master":
        qs = qs.filter(loja__in=lojas)
    status = (request.GET.get("status") or "").strip()
    if status not in StatusPedidoAtacado.values:
        status = ""
    if status:
        qs = qs.filter(status=status)
    busca = (request.GET.get("q") or "").strip()[:100]
    if busca:
        condicao = Q(cliente__nome__icontains=busca)
        if busca.isdecimal():
            condicao |= Q(pk=int(busca)) | Q(orcamento_origem__numero=int(busca))
        qs = qs.filter(condicao)
    pagina = Paginator(qs.order_by("-pk"), 20).get_page(request.GET.get("page"))
    return render(request, "atacado/pedidos_lista.html", {
        "pagina": pagina, "matriz": matriz, "busca": busca, "status_atual": status,
        "status_opcoes": StatusPedidoAtacado.choices,
    })


@login_required
def cancelar_orcamento_atacado_http(request, pk):
    from django.contrib import messages
    from django.core.exceptions import ValidationError
    from django.db import transaction
    from django.shortcuts import redirect
    from django.urls import reverse
    from accounts.permissions import PERMISSAO_ATACADO_GERAR_PEDIDO
    from .models import StatusOrcamentoAtacado
    from .services import transicionar_orcamento
    if request.method != "POST":
        return HttpResponse(status=405)
    matriz, _ = exigir_acesso_comercial(request, PERMISSAO_ATACADO_GERAR_PEDIDO)
    obj = get_object_or_404(
        filtrar_orcamentos_autorizados(
            request, OrcamentoAtacado.objects.all(), PERMISSAO_ATACADO_GERAR_PEDIDO
        ), pk=pk, matriz=matriz
    )
    try:
        with transaction.atomic():
            atual = OrcamentoAtacado.objects.select_for_update().get(pk=obj.pk)
            # F32M5P12F1_MOTIVO: validacao obrigatoria no servidor.
            motivo = (request.POST.get("motivo") or "").strip()
            if len(motivo) < 10 or len(motivo) > 500:
                raise ValidationError("Informe um motivo de cancelamento entre 10 e 500 caracteres.")
            if atual.status not in (StatusOrcamentoAtacado.RASCUNHO, StatusOrcamentoAtacado.ENVIADO):
                raise ValidationError("Somente orcamentos em elaboracao ou enviados podem ser cancelados.")
            if PedidoAtacado.objects.filter(orcamento_origem=atual).exists():
                raise ValidationError("Orcamento com pedido gerado nao pode ser cancelado diretamente.")
            transicionar_orcamento(
                atual, StatusOrcamentoAtacado.CANCELADO, usuario=request.user,
                observacao="Cancelamento: " + motivo
            )
        messages.success(request, "Orcamento cancelado com sucesso.")
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
    destino = reverse("atacado:orcamentos_lista")
    if request.user.is_superuser:
        destino += "?matriz=" + str(matriz.pk)
    return redirect(destino)
