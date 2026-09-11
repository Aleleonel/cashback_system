from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria

from cashback.selectors import (
    get_movimentacoes_cliente,
    get_resumo_extrato_cliente,
    get_saldo_disponivel_cliente,
)

from core.services import get_contexto_operacional_usuario

from .models import Cliente
from .services_cep import consultar_cep

from django.db import models

from django.contrib import messages
from django.shortcuts import redirect

from .forms import (
    ClienteForm,
    ImportarClientesForm,
)

from .services import (
    importar_clientes_validados,
    validar_planilha_clientes,
)

from .importacao import (
    criar_download_modelo_clientes,
)

from .selectors import (
    aplicar_busca_clientes,
    get_cliente_por_cpf,
    obter_cliente_360,
)

from accounts.decorators import require_permission

from accounts.permissions import (
    PERMISSAO_CLIENTES_CRIAR,
    PERMISSAO_CLIENTES_EDITAR,
    PERMISSAO_CLIENTES_IMPORTAR,
    PERMISSAO_CLIENTES_VISUALIZAR,
)

from django.core.paginator import Paginator

@login_required
def consultar_cep_view(request):
    resultado = consultar_cep(request.GET.get('cep', ''))
    return JsonResponse(resultado, status=200 if resultado.get('ok') else 400)

@login_required
@require_permission(PERMISSAO_CLIENTES_VISUALIZAR)
def buscar_cliente_cpf(request):

    cpf = request.GET.get('cpf')

    if not cpf:
        return JsonResponse({'encontrado': False})

    try:
        contexto = get_contexto_operacional_usuario(request.user)

    except ValidationError as erro:
        return JsonResponse({
            'encontrado': False,
            'erro': erro.message
        }, status=400)

    cliente = get_cliente_por_cpf(
        matriz=contexto['matriz'],
        cpf=cpf
    )

    if not cliente:
        return JsonResponse({'encontrado': False})

    saldo_disponivel = get_saldo_disponivel_cliente(
        matriz=contexto['matriz'],
        cliente=cliente
    )
    saldo_disponivel = saldo_disponivel.quantize(Decimal('0.01'))

    return JsonResponse({
        'encontrado': True,
        'cliente_id': cliente.id,
        'nome': cliente.nome,
        'telefone': cliente.telefone or '',
        'email': cliente.email or '',
        'aceita_email': cliente.aceita_email,
        'aceita_sms': cliente.aceita_sms,
        'saldo_disponivel': str(saldo_disponivel),
        'data_nascimento': (
            cliente.data_nascimento.strftime('%d/%m/%Y')
            if cliente.data_nascimento
            else ''
        )
    })

@login_required
@require_permission(PERMISSAO_CLIENTES_VISUALIZAR)
def extrato_cliente(request, cliente_id):

    contexto = get_contexto_operacional_usuario(request.user)

    cliente = get_object_or_404(
        Cliente.objects.select_related(
            'matriz',
            'loja_cadastro'
        ),
        id=cliente_id,
        matriz=contexto['matriz'],
        ativo=True
    )

    secoes_cliente_360 = {"extrato", "compras", "beneficios", "vouchers"}
    dominio_ativo = (request.GET.get("secao") or "extrato").strip().lower()
    if dominio_ativo not in secoes_cliente_360:
        dominio_ativo = "extrato"

    cliente_360 = None
    saldo = None
    movimentacoes = []
    resumo = None

    extrato_page = None
    filtros_extrato = {"data_inicio": "", "data_fim": ""}
    query_string_extrato = ""

    if dominio_ativo == "extrato":
        from datetime import datetime
        from decimal import Decimal
        from django.core.paginator import Paginator
        from django.utils import timezone
        from vouchers.selectors import get_usos_voucher

        data_inicio = (request.GET.get("data_inicio") or "").strip()
        data_fim = (request.GET.get("data_fim") or "").strip()
        filtros_extrato = {"data_inicio": data_inicio, "data_fim": data_fim}
        inicio = None
        fim = None
        try:
            if data_inicio:
                inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()
        except ValueError:
            pass
        try:
            if data_fim:
                fim = datetime.strptime(data_fim, "%Y-%m-%d").date()
        except ValueError:
            pass

        itens_extrato = []
        for item in get_movimentacoes_cliente(matriz=cliente.matriz, cliente=cliente):
            if item.get("tipo") not in {"ENTRADA", "SAIDA"} or item.get("data") is None:
                continue
            data_item = item["data"]
            data_local = timezone.localdate(data_item)
            if inicio is not None and data_local < inicio:
                continue
            if fim is not None and data_local > fim:
                continue
            if item["tipo"] == "ENTRADA":
                valor = item.get("entrada", Decimal("0"))
            else:
                valor = item.get("saida", Decimal("0"))
            itens_extrato.append({
                "data": data_item,
                "tipo": item["tipo"],
                "titulo": item.get("titulo") or "Cashback",
                "loja": item.get("loja"),
                "valor": valor,
            })

        for uso in get_usos_voucher(matriz=cliente.matriz, cliente=cliente):
            data_item = uso.criado_em
            data_local = timezone.localdate(data_item)
            if inicio is not None and data_local < inicio:
                continue
            if fim is not None and data_local > fim:
                continue
            itens_extrato.append({
                "data": data_item,
                "tipo": "VOUCHER",
                "titulo": f"Voucher utilizado - {uso.voucher.codigo} - {uso.voucher.nome}",
                "loja": uso.loja,
                "valor": uso.valor_desconto,
            })

        itens_extrato.sort(key=lambda item: item["data"], reverse=True)
        extrato_page = Paginator(itens_extrato, 20).get_page(request.GET.get("page"))
        query_params_extrato = request.GET.copy()
        query_params_extrato["secao"] = "extrato"
        query_params_extrato.pop("page", None)
        query_string_extrato = query_params_extrato.urlencode()

    compras_page = None
    filtros_compras = {"data_inicio": "", "data_fim": "", "loja": ""}
    lojas_compras = []
    query_string_compras = ""

    if dominio_ativo == "compras":
        from datetime import datetime
        from django.core.paginator import Paginator
        from empresas.models import Loja
        from pdv.models import Venda

        vendas_compras = (
            Venda.objects
            .filter(
                cliente=cliente,
                matriz=cliente.matriz,
                status="finalizada",
            )
            .select_related("loja")
            .order_by("-finalizada_em", "-id")
        )

        data_inicio = (request.GET.get("data_inicio") or "").strip()
        data_fim = (request.GET.get("data_fim") or "").strip()
        loja_id = (request.GET.get("loja") or "").strip()

        filtros_compras = {
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "loja": loja_id,
        }

        if data_inicio:
            try:
                inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()
            except ValueError:
                inicio = None
            if inicio is not None:
                vendas_compras = vendas_compras.filter(
                    finalizada_em__date__gte=inicio
                )

        if data_fim:
            try:
                fim = datetime.strptime(data_fim, "%Y-%m-%d").date()
            except ValueError:
                fim = None
            if fim is not None:
                vendas_compras = vendas_compras.filter(
                    finalizada_em__date__lte=fim
                )

        lojas_compras = Loja.objects.filter(
            matriz=cliente.matriz
        ).order_by("nome")

        if loja_id.isdigit():
            loja_transacao = lojas_compras.filter(pk=int(loja_id)).first()
            if loja_transacao is not None:
                vendas_compras = vendas_compras.filter(loja=loja_transacao)

        compras_page = Paginator(vendas_compras, 20).get_page(
            request.GET.get("page")
        )

        query_params = request.GET.copy()
        query_params["secao"] = "compras"
        query_params.pop("page", None)
        query_string_compras = query_params.urlencode()

    beneficios_page = None
    filtros_beneficios = {
        "data_inicio": "",
        "data_fim": "",
    }
    query_string_beneficios = ""

    if dominio_ativo == "beneficios":
        from datetime import datetime
        from django.core.paginator import Paginator
        from django.utils import timezone

        data_inicio = (request.GET.get("data_inicio") or "").strip()
        data_fim = (request.GET.get("data_fim") or "").strip()

        filtros_beneficios = {
            "data_inicio": data_inicio,
            "data_fim": data_fim,
        }

        inicio = None
        fim = None

        if data_inicio:
            try:
                inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()
            except ValueError:
                inicio = None

        if data_fim:
            try:
                fim = datetime.strptime(data_fim, "%Y-%m-%d").date()
            except ValueError:
                fim = None

        movimentacoes_cashback = [
            item
            for item in get_movimentacoes_cliente(
                matriz=cliente.matriz,
                cliente=cliente,
            )
            if item.get("tipo") in {"ENTRADA", "SAIDA"}
        ]
        resumo = get_resumo_extrato_cliente(
            matriz=cliente.matriz,
            cliente=cliente,
        )


        if inicio is not None:
            movimentacoes_cashback = [
                item
                for item in movimentacoes_cashback
                if timezone.localdate(item["data"]) >= inicio
            ]

        if fim is not None:
            movimentacoes_cashback = [
                item
                for item in movimentacoes_cashback
                if timezone.localdate(item["data"]) <= fim
            ]

        beneficios_page = Paginator(
            movimentacoes_cashback,
            20,
        ).get_page(
            request.GET.get("page")
        )

        query_params = request.GET.copy()
        query_params["secao"] = "beneficios"
        query_params.pop("page", None)
        query_string_beneficios = query_params.urlencode()

    usos_vouchers_page = None
    filtros_usos_vouchers = {"data_inicio": "", "data_fim": ""}
    query_string_usos_vouchers = ""

    vouchers_page = None
    filtros_vouchers = {
        "data_inicio": "",
        "data_fim": "",
        "status": "",
    }
    query_string_vouchers = ""

    if dominio_ativo == "vouchers":
        from datetime import datetime
        from django.core.paginator import Paginator
        from django.db.models import Q
        from django.utils import timezone
        from vouchers.models import Voucher

        data_inicio = (request.GET.get("data_inicio") or "").strip()
        data_fim = (request.GET.get("data_fim") or "").strip()
        status_voucher = (request.GET.get("status") or "").strip()

        filtros_vouchers = {
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "status": status_voucher,
        }

        vouchers = (
            Voucher.objects.filter(matriz=contexto["matriz"])
            .filter(Q(cliente=cliente) | Q(cliente__isnull=True))
            .order_by("-data_fim", "-id")
        )

        inicio = None
        fim = None
        if data_inicio:
            try:
                inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()
            except ValueError:
                inicio = None
        if data_fim:
            try:
                fim = datetime.strptime(data_fim, "%Y-%m-%d").date()
            except ValueError:
                fim = None

        if inicio is not None:
            vouchers = vouchers.filter(data_fim__gte=inicio)
        if fim is not None:
            vouchers = vouchers.filter(data_inicio__lte=fim)

        status_validos = {Voucher.Status.ATIVO, Voucher.Status.INATIVO}
        if status_voucher in status_validos:
            vouchers = vouchers.filter(status=status_voucher)

        vouchers_page = Paginator(vouchers, 20).get_page(request.GET.get("page"))

        query_params = request.GET.copy()
        query_params["secao"] = "vouchers"
        query_params.pop("page", None)
        query_string_vouchers = query_params.urlencode()

        from vouchers.selectors import get_usos_voucher
        data_inicio_usos = (request.GET.get("data_inicio_usos") or "").strip()
        data_fim_usos = (request.GET.get("data_fim_usos") or "").strip()
        filtros_usos_vouchers = {"data_inicio": data_inicio_usos, "data_fim": data_fim_usos}
        inicio_usos = fim_usos = None
        try:
            if data_inicio_usos:
                inicio_usos = datetime.strptime(data_inicio_usos, "%Y-%m-%d").date()
        except ValueError:
            pass
        try:
            if data_fim_usos:
                fim_usos = datetime.strptime(data_fim_usos, "%Y-%m-%d").date()
        except ValueError:
            pass
        usos_vouchers = get_usos_voucher(matriz=cliente.matriz, cliente=cliente)
        if inicio_usos is not None or fim_usos is not None:
            usos_vouchers = [
                uso for uso in usos_vouchers
                if (inicio_usos is None or timezone.localdate(uso.criado_em) >= inicio_usos)
                and (fim_usos is None or timezone.localdate(uso.criado_em) <= fim_usos)
            ]
        usos_vouchers_page = Paginator(usos_vouchers, 20).get_page(request.GET.get("page_usos"))
        query_params_usos = request.GET.copy()
        query_params_usos["secao"] = "vouchers"
        query_params_usos.pop("page_usos", None)
        query_string_usos_vouchers = query_params_usos.urlencode()

    return render(
        request,
        'clientes/extrato_cliente.html',
        {
            'cliente': cliente,
            'saldo': saldo,
            'movimentacoes': movimentacoes,
            'resumo': resumo,
            'cliente_360': cliente_360,
            'dominio_ativo': dominio_ativo,
            'extrato_page': extrato_page,
            'filtros_extrato': filtros_extrato,
            'query_string_extrato': query_string_extrato,
            'compras_page': compras_page,
            'filtros_compras': filtros_compras,
            'lojas_compras': lojas_compras,
            'query_string_compras': query_string_compras,
            'beneficios_page': beneficios_page,
            'filtros_beneficios': filtros_beneficios,
            'query_string_beneficios': query_string_beneficios,
            'vouchers_page': vouchers_page,
            'filtros_vouchers': filtros_vouchers,
            'query_string_vouchers': query_string_vouchers,
            'usos_vouchers_page': usos_vouchers_page,
            'filtros_usos_vouchers': filtros_usos_vouchers,
            'query_string_usos_vouchers': query_string_usos_vouchers,
        }
    )

@login_required
@require_permission(PERMISSAO_CLIENTES_VISUALIZAR)
def detalhe_compra_cliente(request, cliente_id, venda_id):
    from decimal import Decimal
    from django.db.models import Sum
    from django.db.models.functions import Coalesce
    from pdv.models import Venda

    contexto = get_contexto_operacional_usuario(request.user)

    cliente = get_object_or_404(
        Cliente.objects.select_related("matriz", "loja_cadastro"),
        id=cliente_id,
        matriz=contexto["matriz"],
        ativo=True,
    )

    venda = get_object_or_404(
        Venda.objects
        .select_related("matriz", "loja", "cliente", "operador", "vendedor")
        .prefetch_related(
            "itens__produto",
            "itens__cancelado_por",
            "pagamentos__forma_pagamento",
            "pagamentos__autorizado_por",
        ),
        id=venda_id,
        cliente=cliente,
        matriz=cliente.matriz,
        status="finalizada",
    )

    itens = venda.itens.select_related(
        "produto",
        "cancelado_por",
    ).order_by("sequencia")

    pagamentos = (
        venda.pagamentos
        .select_related("forma_pagamento", "autorizado_por")
        .order_by("criado_em", "id")
    )

    resumo_pagamentos = pagamentos.aggregate(
        total_pago=Coalesce(Sum("valor"), Decimal("0.00")),
        total_troco=Coalesce(Sum("troco"), Decimal("0.00")),
    )

    return render(
        request,
        "clientes/detalhe_compra_cliente.html",
        {
            "cliente": cliente,
            "venda": venda,
            "itens": itens,
            "pagamentos": pagamentos,
            "resumo_pagamentos": resumo_pagamentos,
        },
    )


@login_required
@require_permission(PERMISSAO_CLIENTES_VISUALIZAR)
def lista_clientes(request):

    contexto = get_contexto_operacional_usuario(
        request.user
    )

    busca = request.GET.get('q', '').strip()

    clientes = Cliente.objects.filter(
        matriz=contexto['matriz'],
        ativo=True
    ).only(
        'id',
        'nome',
        'nome_normalizado',
        'cpf',
        'cpf_normalizado',
        'telefone',
        'telefone_normalizado',
        'email',
        'email_normalizado',
    )

    if busca:
        clientes = aplicar_busca_clientes(
            clientes,
            busca
        )

    clientes = clientes.order_by('nome')

    paginator = Paginator(clientes, 50)

    page = request.GET.get('page')

    clientes = paginator.get_page(page)

    return render(
        request,
        'clientes/lista_clientes.html',
        {
            'clientes': clientes,
            'busca': busca,
        }
    )

@login_required
@require_permission(PERMISSAO_CLIENTES_CRIAR)
def criar_cliente(request):

    contexto = get_contexto_operacional_usuario(request.user)

    if request.method == 'POST':
        form = ClienteForm(request.POST)
        form.instance.matriz = contexto['matriz']
        form.instance.loja_cadastro = contexto['loja']

        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.matriz = contexto['matriz']
            cliente.loja_cadastro = contexto['loja']

            cliente.save()

            registrar_auditoria(
                usuario=request.user,
                matriz=contexto['matriz'],
                loja=contexto['loja'],
                acao=RegistroAuditoria.ACAO_CRIAR,
                recurso='clientes.cliente',
                recurso_id=cliente.id,
                descricao=f'Cliente criado: {cliente.nome}',
                request=request
            )

            messages.success(request, 'Cliente cadastrado com sucesso.')

            return redirect('clientes:lista_clientes')

    else:
        form = ClienteForm()

    return render(
        request,
        'clientes/form_cliente.html',
        {
            'form': form,
            'titulo': 'Novo Cliente',
        }
    )

@login_required
@require_permission(PERMISSAO_CLIENTES_EDITAR)
def editar_cliente(request, cliente_id):

    contexto = get_contexto_operacional_usuario(request.user)

    cliente = get_object_or_404(
        Cliente.objects.select_related('matriz', 'loja_cadastro'),
        id=cliente_id,
        matriz=contexto['matriz'],
    )

    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)

        if form.is_valid():
            cliente = form.save()

            registrar_auditoria(
                usuario=request.user,
                matriz=contexto['matriz'],
                loja=contexto['loja'],
                acao=RegistroAuditoria.ACAO_EDITAR,
                recurso='clientes.cliente',
                recurso_id=cliente.id,
                descricao=f'Cliente editado: {cliente.nome}',
                request=request
            )

            messages.success(request, 'Cliente atualizado com sucesso.')

            return redirect('clientes:lista_clientes')

    else:
        form = ClienteForm(instance=cliente)

    return render(
        request,
        'clientes/form_cliente.html',
        {
            'form': form,
            'titulo': 'Editar Cliente',
            'cliente': cliente,
        }
    )

@login_required
@require_permission(PERMISSAO_CLIENTES_IMPORTAR)
def importar_clientes(request):

    contexto = get_contexto_operacional_usuario(request.user)

    if request.method == 'POST':
        form = ImportarClientesForm(request.POST, request.FILES)

        if form.is_valid():
            resultado = validar_planilha_clientes(
                arquivo=form.cleaned_data['arquivo'],
                matriz=contexto['matriz']
            )

            if not resultado['valido']:
                messages.error(request, resultado['erro_estrutura'])

            else:
                resultado['possui_validos'] = (
                    resultado['resumo']['validos'] > 0
                )

                request.session['importacao_clientes_linhas'] = resultado['linhas']

                return render(
                    request,
                    'clientes/confirmar_importacao.html',
                    {
                        'resultado': resultado,
                    }
                )

    else:
        form = ImportarClientesForm()

    return render(
        request,
        'clientes/importar_clientes.html',
        {
            'form': form,
        }
    )

@login_required
@require_permission(PERMISSAO_CLIENTES_IMPORTAR)
def confirmar_importacao_clientes(request):

    contexto = get_contexto_operacional_usuario(request.user)

    linhas = request.session.get('importacao_clientes_linhas')

    if not linhas:
        messages.error(request, 'Nenhuma importação pendente encontrada.')

        return redirect('clientes:importar_clientes')

    resultado = importar_clientes_validados(
        matriz=contexto['matriz'],
        loja=contexto['loja'],
        linhas=linhas
    )
    
    registrar_auditoria(
        usuario=request.user,
        matriz=contexto['matriz'],
        loja=contexto['loja'],
        acao=RegistroAuditoria.ACAO_IMPORTAR,
        recurso='clientes.importacao',
        descricao=(
            f"Importação de clientes concluída. "
            f"Criados: {resultado['criados']}. "
            f"Atualizados: {resultado['atualizados']}."
        ),
        request=request
    )

    del request.session['importacao_clientes_linhas']

    messages.success(
        request,
        f"Importação concluída. Criados: {resultado['criados']}. Atualizados: {resultado['atualizados']}."
    )

    return redirect('clientes:lista_clientes')

@login_required
@require_permission(PERMISSAO_CLIENTES_IMPORTAR)
def baixar_modelo_importacao_clientes(request):
    return criar_download_modelo_clientes()
