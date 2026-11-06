from .forms_atacado import FaixaAtacadoFormSet, PoliticaAtacadoForm
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import require_permission
from accounts.permissions import PERMISSAO_EMPRESA_USUARIOS_GERENCIAR, PERMISSAO_FINANCEIRO_LANCAR_DESPESA, PERMISSAO_FINANCEIRO_VISUALIZAR
from accounts.services import usuario_tem_permissao

from .catalogo import listar_grupos_configuracao
from .forms import ConfiguracaoComissaoMatrizForm, MetaComissaoLojaForm, ConfiguracaoComercialForm, FormaPagamentoForm
from pdv.models import FormaPagamento
from empresas.models import Matriz
from .services import (
    atualizar_configuracao_comercial,
    obter_ou_criar_configuracao_comercial,
    criar_forma_pagamento,
    atualizar_forma_pagamento,
)
from .decorators import (
    central_configuracoes_required,
    configuracoes_criticas_required,
)


@central_configuracoes_required
def inicio(request):
    contexto_acesso = request.contexto_configuracoes
    grupos = listar_grupos_configuracao(
        incluir_criticos=contexto_acesso["pode_configuracoes_criticas"]
    )

    return render(
        request,
        "configuracoes/inicio.html",
        {
            "grupos": grupos,
            "contexto_configuracoes": contexto_acesso,
        },
    )


@configuracoes_criticas_required
def criticas(request):
    return render(
        request,
        "configuracoes/criticas.html",
        {
            "contexto_configuracoes": request.contexto_configuracoes,
        },
    )

@central_configuracoes_required
def empresa(request):
    contexto_acesso = request.contexto_configuracoes

    return render(
        request,
        "configuracoes/empresa.html",
        {
            "contexto_configuracoes": contexto_acesso,
            "pode_operar_empresa": (
                contexto_acesso["escopo"] == "empresa"
                and contexto_acesso["matriz"] is not None
            ),
        },
    )

@central_configuracoes_required
@require_permission(PERMISSAO_EMPRESA_USUARIOS_GERENCIAR)
def usuarios_permissoes(request):
    contexto_acesso = request.contexto_configuracoes

    return render(
        request,
        "configuracoes/usuarios_permissoes.html",
        {
            "contexto_configuracoes": contexto_acesso,
            "pode_operar_usuarios": (
                contexto_acesso["escopo"] == "empresa"
                and contexto_acesso["matriz"] is not None
            ),
        },
    )

@central_configuracoes_required
def clientes_cashback(request):
    contexto_acesso = request.contexto_configuracoes

    return render(
        request,
        "configuracoes/clientes_cashback.html",
        {
            "contexto_configuracoes": contexto_acesso,
            "pode_operar_clientes_cashback": (
                contexto_acesso["escopo"] == "empresa"
                and contexto_acesso["matriz"] is not None
            ),
        },
    )

@central_configuracoes_required
def vendas_comissoes(request):
    contexto_acesso = request.contexto_configuracoes

    secoes = [
        {
            "titulo": "Regras Comerciais",
            "descricao": "Parâmetros gerais que orientam vendas, descontos e condições comerciais.",
            "icone": "bi-sliders",
            "url_name": "configuracoes:regras_comerciais",
            "disponivel": True,
        },
        {
            "titulo": "Tabelas de Preços",
            "descricao": "Organização das tabelas e políticas de preços utilizadas pelo sistema.",
            "icone": "bi-tags",
        },
        {
            "titulo": "Promoções",
            "descricao": "Central futura para campanhas promocionais e condições especiais.",
            "icone": "bi-megaphone",
        },
        {
            "titulo": "Atacado",
            "descricao": "Faixas progressivas, elegibilidade promocional e politica de vendas no atacado.",
            "icone": "bi-box-seam",
            "url_name": "configuracoes:politica_atacado",
            "disponivel": True,
        },
        {
            "titulo": "Cashback Comercial",
            "descricao": "Integração futura das regras comerciais com benefícios de cashback.",
            "icone": "bi-arrow-repeat",
        },
        {
            "titulo": "Voucher",
            "descricao": "Configurações futuras de vouchers, validade e regras de utilização.",
            "icone": "bi-ticket-perforated",
        },
        {
            "titulo": "Brindes",
            "descricao": "Critérios futuros para concessão e controle de brindes nas vendas.",
            "icone": "bi-gift",
        },
        {
            "titulo": "Comissões",
            "descricao": "Configure elegibilidade, metas por loja e fechamento mensal de comissões.",
            "icone": "bi-percent",
            "url_name": "configuracoes:comissoes",
            "disponivel": True,
        },
    ]

    return render(
        request,
        "configuracoes/vendas_comissoes.html",
        {
            "contexto_configuracoes": contexto_acesso,
            "secoes": secoes,
        },
    )

@central_configuracoes_required
def comissoes(request):
    from .models import ConfiguracaoComissaoMatriz, MetaComissaoLoja, FechamentoComissao
    from empresas.models import Loja, Matriz
    contexto_acesso = request.contexto_configuracoes
    matrizes_plataforma = Matriz.objects.none()
    erro_matriz = None
    if contexto_acesso["escopo"] == "empresa":
        matriz = contexto_acesso["matriz"]
    else:
        matriz = None
        matrizes_plataforma = Matriz.objects.all().order_by("nome")
        matriz_id = request.GET.get("matriz", "").strip()
        if matriz_id:
            try:
                matriz = matrizes_plataforma.get(pk=int(matriz_id))
            except (TypeError, ValueError, Matriz.DoesNotExist):
                erro_matriz = "Matriz selecionada inválida."
    lojas = Loja.objects.filter(matriz=matriz).order_by("nome") if matriz else Loja.objects.none()
    configuracao = ConfiguracaoComissaoMatriz.objects.filter(matriz=matriz).get() if matriz is not None and ConfiguracaoComissaoMatriz.objects.filter(matriz=matriz).exists() else None
    form_configuracao = ConfiguracaoComissaoMatrizForm(instance=configuracao) if matriz is not None else None
    meta_form = MetaComissaoLojaForm()
    if matriz is not None and request.method == "POST":
        acao = request.POST.get("acao")
        redirect_comissoes = f"{request.path}?matriz={matriz.pk}" if contexto_acesso["escopo"] == "plataforma" else request.path
        if acao == "salvar_configuracao":
            form_configuracao = ConfiguracaoComissaoMatrizForm(request.POST, instance=configuracao)
            if form_configuracao.is_valid():
                obj = form_configuracao.save(commit=False)
                obj.matriz = matriz
                obj.save()
                messages.success(request, "Configuração de comissão atualizada com sucesso.")
                return redirect(redirect_comissoes)
        elif acao == "adicionar_meta":
            loja_id = request.POST.get("loja_id")
            try:
                loja = lojas.get(pk=loja_id)
            except (Loja.DoesNotExist, TypeError, ValueError):
                messages.error(request, "Loja inválida para o contexto selecionado.")
            else:
                meta_form = MetaComissaoLojaForm(request.POST)
                if meta_form.is_valid():
                    meta = meta_form.save(commit=False)
                    meta.loja = loja
                    meta.save()
                    messages.success(request, "Meta de comissão adicionada com sucesso.")
                    return redirect(redirect_comissoes)
        elif acao == "provisionar_comissao":
            if not usuario_tem_permissao(request.user, PERMISSAO_FINANCEIRO_LANCAR_DESPESA):
                messages.error(request, "Voce nao tem permissao para provisionar comissoes no Financeiro.")
                return redirect(redirect_comissoes)
            from datetime import date
            from django.core.exceptions import ValidationError
            from .models import ComissaoVendedor
            from .services_comissoes import gerar_titulo_financeiro_comissao
            comissao_id = request.POST.get("comissao_id")
            vencimento_raw = (request.POST.get("vencimento") or "").strip()
            try:
                vencimento = date.fromisoformat(vencimento_raw)
            except (TypeError, ValueError):
                messages.error(request, "Informe um vencimento valido para provisionar a comissao.")
                return redirect(redirect_comissoes)
            try:
                comissao = ComissaoVendedor.objects.select_related("fechamento__loja", "fechamento__matriz").get(pk=comissao_id, fechamento__loja__in=lojas)
            except (ComissaoVendedor.DoesNotExist, TypeError, ValueError):
                messages.error(request, "Comissao invalida para o contexto selecionado.")
            else:
                try:
                    gerar_titulo_financeiro_comissao(comissao=comissao, vencimento=vencimento, usuario=request.user, request=request)
                except ValidationError as exc:
                    messages.error(request, "; ".join(exc.messages))
                else:
                    messages.success(request, "Comissao provisionada no Financeiro com sucesso.")
                    return redirect(redirect_comissoes)
        elif acao == "provisionar_comissao_parceiro":
            if not usuario_tem_permissao(request.user, PERMISSAO_FINANCEIRO_LANCAR_DESPESA):
                messages.error(request, "Voce nao tem permissao para provisionar comissoes no Financeiro.")
                return redirect(redirect_comissoes)
            from datetime import date
            from django.core.exceptions import ValidationError
            from vouchers.models import ComissaoParceiro
            from .services_comissoes import gerar_titulo_financeiro_comissao_parceiro
            comissao_parceiro_id = request.POST.get("comissao_parceiro_id")
            try:
                vencimento = date.fromisoformat((request.POST.get("vencimento") or "").strip())
            except (TypeError, ValueError):
                messages.error(request, "Informe um vencimento valido para provisionar a comissao do parceiro.")
                return redirect(redirect_comissoes)
            try:
                comissao_parceiro = ComissaoParceiro.objects.select_related("parceiro", "uso_voucher__voucher", "uso_voucher__loja").get(pk=comissao_parceiro_id, matriz=matriz)
            except (ComissaoParceiro.DoesNotExist, TypeError, ValueError):
                messages.error(request, "Comissao de parceiro invalida para o contexto selecionado.")
            else:
                try:
                    gerar_titulo_financeiro_comissao_parceiro(comissao=comissao_parceiro, vencimento=vencimento, usuario=request.user, request=request)
                except ValidationError as exc:
                    messages.error(request, "; ".join(exc.messages))
                else:
                    messages.success(request, "Comissao do parceiro provisionada no Financeiro com sucesso.")
                    return redirect(redirect_comissoes)
        elif acao == "fechamento_comissao":
            from .services_comissoes import fechar_comissoes_competencia
            loja_fechamento_id = request.POST.get("loja_fechamento_id")
            competencia_ano = request.POST.get("competencia_ano")
            competencia_mes = request.POST.get("competencia_mes")
            try:
                ano = int(competencia_ano)
                mes = int(competencia_mes)
                if ano < 1 or mes < 1 or mes > 12:
                    raise ValueError
                fechamento_global = loja_fechamento_id == "todas"
                loja_fechamento = None if fechamento_global else lojas.get(pk=loja_fechamento_id)
            except (Loja.DoesNotExist, TypeError, ValueError):
                messages.error(request, "Loja ou competência inválida para o fechamento.")
            else:
                if fechamento_global:
                    lojas_fechadas = list(lojas)
                    with transaction.atomic():
                        for loja_alvo in lojas_fechadas:
                            fechar_comissoes_competencia(loja=loja_alvo, ano=ano, mes=mes)
                    messages.success(request, f"Fechamento de {mes:02d}/{ano} disponível no histórico para {len(lojas_fechadas)} loja(s).")
                else:
                    fechar_comissoes_competencia(loja=loja_fechamento, ano=ano, mes=mes)
                    messages.success(request, f"Fechamento de {mes:02d}/{ano} para {loja_fechamento.nome} disponível no histórico.")
                return redirect(redirect_comissoes)
    from vouchers.models import ComissaoParceiro
    metas = MetaComissaoLoja.objects.filter(loja__in=lojas).order_by("loja__nome", "valor_meta") if matriz else MetaComissaoLoja.objects.none()
    from django.utils import timezone
    hoje = timezone.localdate()

    try:
        historico_ano = int(request.GET.get("historico_ano", hoje.year))
        historico_mes = int(request.GET.get("historico_mes", hoje.month))
        if historico_ano < 1 or not 1 <= historico_mes <= 12:
            raise ValueError
    except (TypeError, ValueError):
        historico_ano = hoje.year
        historico_mes = hoje.month

    fechamentos_comissao = (
        FechamentoComissao.objects.filter(
            loja__in=lojas,
            competencia_ano=historico_ano,
            competencia_mes=historico_mes,
        )
        .select_related("loja")
        .prefetch_related("comissoes_vendedores")
        .order_by("loja__nome", "-pk")
        if matriz
        else FechamentoComissao.objects.none()
    )
    competencia_historico = f"{historico_mes:02d}/{historico_ano}"
    from financeiro.models import TituloFinanceiro
    titulos_comissao = {titulo.origem_id: titulo for titulo in TituloFinanceiro.objects.filter(matriz=matriz, loja__in=lojas, natureza=TituloFinanceiro.Natureza.PAGAR, origem_tipo=TituloFinanceiro.OrigemTipo.COMISSAO)} if matriz else {}
    for fechamento in fechamentos_comissao:
        for comissao in fechamento.comissoes_vendedores.all():
            comissao.titulo_financeiro = titulos_comissao.get(str(comissao.pk))
    from .services_comissoes_parceiros import consolidar_comissoes_parceiros, listar_detalhes_comissoes_parceiro
    try:
        competencia_ano_parceiros = int(request.GET.get("parceiros_ano", hoje.year))
        competencia_mes_parceiros = int(request.GET.get("parceiros_mes", hoje.month))
        if competencia_ano_parceiros < 1 or not 1 <= competencia_mes_parceiros <= 12:
            raise ValueError
    except (TypeError, ValueError):
        competencia_ano_parceiros = hoje.year
        competencia_mes_parceiros = hoje.month
    competencia_parceiros = f"{competencia_mes_parceiros:02d}/{competencia_ano_parceiros}"
    comissoes_parceiros_consolidadas = (
        consolidar_comissoes_parceiros(matriz=matriz, ano=competencia_ano_parceiros, mes=competencia_mes_parceiros)
        if matriz else []
    )
    parceiro_detalhes = None
    parceiro_detalhes_id = request.GET.get("parceiro_detalhes", "").strip()
    if matriz and parceiro_detalhes_id:
        try:
            parceiro_detalhes_id = int(parceiro_detalhes_id)
            parceiro_detalhes_pagina = int(request.GET.get("parceiro_pagina", 1))
        except (TypeError, ValueError):
            parceiro_detalhes_id = None
            parceiro_detalhes_pagina = 1
        if parceiro_detalhes_id:
            parceiro_detalhes = listar_detalhes_comissoes_parceiro(
                matriz=matriz,
                parceiro_id=parceiro_detalhes_id,
                ano=competencia_ano_parceiros,
                mes=competencia_mes_parceiros,
                pagina=parceiro_detalhes_pagina,
                por_pagina=20,
            )
    pode_provisionar_comissao = usuario_tem_permissao(request.user, PERMISSAO_FINANCEIRO_LANCAR_DESPESA)
    pode_visualizar_financeiro = usuario_tem_permissao(request.user, PERMISSAO_FINANCEIRO_VISUALIZAR)
    return render(request, "configuracoes/comissoes.html", {"contexto_configuracoes": contexto_acesso, "matriz": matriz, "matrizes_plataforma": matrizes_plataforma, "erro_matriz": erro_matriz, "lojas": lojas, "configuracao_comissao": configuracao, "form_configuracao": form_configuracao, "metas": metas, "meta_form": meta_form, "fechamentos_comissao": fechamentos_comissao, "historico_mes": historico_mes, "historico_ano": historico_ano, "competencia_historico": competencia_historico, "comissoes_parceiros_consolidadas": comissoes_parceiros_consolidadas, "competencia_parceiros": competencia_parceiros, "competencia_ano_parceiros": competencia_ano_parceiros, "competencia_mes_parceiros": competencia_mes_parceiros, "parceiro_detalhes": parceiro_detalhes, "parceiro_detalhes_id": parceiro_detalhes_id, "pode_provisionar_comissao": pode_provisionar_comissao, "pode_visualizar_financeiro": pode_visualizar_financeiro})

@central_configuracoes_required
def meta_comissao_editar(request, pk):
    from .models import MetaComissaoLoja
    from empresas.models import Matriz
    contexto_acesso = request.contexto_configuracoes
    if contexto_acesso["escopo"] == "empresa":
        matriz = contexto_acesso["matriz"]
    else:
        matriz = None
        matriz_id = request.GET.get("matriz", "").strip()
        if matriz_id:
            try:
                matriz = Matriz.objects.get(pk=int(matriz_id))
            except (TypeError, ValueError, Matriz.DoesNotExist):
                matriz = None
    if matriz is None:
        messages.error(request, "Selecione uma matriz válida para editar a meta.")
        return redirect("configuracoes:comissoes")
    meta = get_object_or_404(MetaComissaoLoja, pk=pk, loja__matriz=matriz)
    form = MetaComissaoLojaForm(request.POST or None, instance=meta)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Meta de comissão atualizada com sucesso.")
        destino = reverse("configuracoes:comissoes")
        if contexto_acesso["escopo"] == "plataforma":
            destino = f"{destino}?matriz={matriz.pk}"
        return redirect(destino)
    return render(request, "configuracoes/meta_comissao_form.html", {"contexto_configuracoes": contexto_acesso, "matriz": matriz, "meta": meta, "form": form})


@central_configuracoes_required
def regras_comerciais(request):
    contexto_acesso = request.contexto_configuracoes
    matriz = contexto_acesso["matriz"]
    pode_editar = (
        contexto_acesso["escopo"] == "empresa"
        and matriz is not None
    )

    configuracao = None
    if matriz is not None:
        configuracao = obter_ou_criar_configuracao_comercial(matriz=matriz)

    if request.method == "POST":
        if not pode_editar or configuracao is None:
            messages.error(
                request,
                "Selecione um contexto de empresa válido para alterar as regras comerciais.",
            )
            return redirect("configuracoes:regras_comerciais")

        form = ConfiguracaoComercialForm(
            request.POST,
            instance=configuracao,
            pode_editar=True,
        )
        if form.is_valid():
            atualizar_configuracao_comercial(
                configuracao=configuracao,
                dados=form.cleaned_data,
            )
            messages.success(request, "Regras comerciais atualizadas com sucesso.")
            return redirect("configuracoes:regras_comerciais")
    else:
        form = ConfiguracaoComercialForm(
            instance=configuracao,
            pode_editar=pode_editar,
        )

    return render(
        request,
        "configuracoes/regras_comerciais.html",
        {
            "contexto_configuracoes": contexto_acesso,
            "configuracao": configuracao,
            "form": form,
            "pode_editar_regras": pode_editar,
        },
    )



def _contexto_formas_pagamento(request):
    contexto = request.contexto_configuracoes
    if contexto["escopo"] == "empresa":
        return contexto["matriz"], Matriz.objects.none(), None
    matriz_id = request.GET.get("matriz", "").strip()
    matrizes = Matriz.objects.all().order_by("nome")
    if not matriz_id:
        return None, matrizes, None
    try:
        matriz = matrizes.get(pk=int(matriz_id))
    except (TypeError, ValueError, Matriz.DoesNotExist):
        return None, matrizes, "Matriz selecionada inválida."
    return matriz, matrizes, None

@central_configuracoes_required
def formas_pagamento(request):
    contexto=request.contexto_configuracoes
    matriz, matrizes_plataforma, erro_matriz=_contexto_formas_pagamento(request)
    formas=FormaPagamento.objects.filter(matriz=matriz).order_by("nome") if matriz else FormaPagamento.objects.none()
    return render(request,"configuracoes/formas_pagamento.html",{"contexto_configuracoes":contexto,"matriz_alvo":matriz,"matrizes_plataforma":matrizes_plataforma,"erro_matriz":erro_matriz,"formas_pagamento":formas,"pode_editar_formas":matriz is not None})

@central_configuracoes_required
def forma_pagamento_criar(request):
    contexto=request.contexto_configuracoes
    matriz, _, erro=_contexto_formas_pagamento(request)
    if matriz is None:
        messages.error(request,erro or "Selecione explicitamente uma matriz para cadastrar formas de pagamento.")
        return redirect("configuracoes:formas_pagamento")
    form=FormaPagamentoForm(request.POST or None)
    if request.method=="POST" and form.is_valid():
        criar_forma_pagamento(matriz=matriz,dados=form.cleaned_data,usuario=request.user,request=request)
        messages.success(request,"Forma de pagamento cadastrada com sucesso.")
        if contexto["escopo"]=="plataforma": return redirect(f"{reverse('configuracoes:formas_pagamento')}?matriz={matriz.pk}")
        return redirect("configuracoes:formas_pagamento")
    return render(request,"configuracoes/forma_pagamento_form.html",{"contexto_configuracoes":contexto,"matriz_alvo":matriz,"form":form,"titulo_pagina":"Nova forma de pagamento"})

@central_configuracoes_required
def forma_pagamento_editar(request,pk):
    contexto=request.contexto_configuracoes
    matriz, _, erro=_contexto_formas_pagamento(request)
    if matriz is None:
        messages.error(request,erro or "Selecione explicitamente uma matriz para alterar formas de pagamento.")
        return redirect("configuracoes:formas_pagamento")
    forma=get_object_or_404(FormaPagamento,pk=pk,matriz=matriz)
    form=FormaPagamentoForm(request.POST or None,instance=forma)
    if request.method=="POST" and form.is_valid():
        atualizar_forma_pagamento(forma=forma,dados=form.cleaned_data,usuario=request.user,request=request)
        messages.success(request,"Forma de pagamento atualizada com sucesso.")
        if contexto["escopo"]=="plataforma": return redirect(f"{reverse('configuracoes:formas_pagamento')}?matriz={matriz.pk}")
        return redirect("configuracoes:formas_pagamento")
    return render(request,"configuracoes/forma_pagamento_form.html",{"contexto_configuracoes":contexto,"matriz_alvo":matriz,"form":form,"forma_pagamento":forma,"titulo_pagina":"Editar forma de pagamento"})

@central_configuracoes_required
def politica_atacado(request):
    contexto_acesso = request.contexto_configuracoes
    matriz = contexto_acesso["matriz"]
    pode_editar = contexto_acesso["escopo"] == "empresa" and matriz is not None
    configuracao = obter_ou_criar_configuracao_comercial(matriz=matriz) if matriz is not None else None

    if request.method == "POST":
        if not pode_editar or configuracao is None:
            messages.error(
                request,
                "Selecione um contexto de empresa valido para alterar a politica de atacado.",
            )
            return redirect("configuracoes:politica_atacado")
        form = PoliticaAtacadoForm(request.POST, instance=configuracao, pode_editar=True)
        formset = FaixaAtacadoFormSet(request.POST, instance=configuracao, prefix="faixas")
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                configuracao = form.save()
                formset.instance = configuracao
                formset.save()
            messages.success(request, "Politica de atacado atualizada com sucesso.")
            return redirect("configuracoes:politica_atacado")
    else:
        form = PoliticaAtacadoForm(instance=configuracao, pode_editar=pode_editar)
        formset = (
            FaixaAtacadoFormSet(instance=configuracao, prefix="faixas")
            if configuracao is not None else None
        )

    if formset is not None and not pode_editar:
        for faixa_form in formset.forms:
            for campo in faixa_form.fields.values():
                campo.disabled = True

    return render(
        request,
        "configuracoes/politica_atacado.html",
        {
            "contexto_configuracoes": contexto_acesso,
            "configuracao": configuracao,
            "form": form,
            "formset": formset,
            "pode_editar_atacado": pode_editar,
        },
    )
