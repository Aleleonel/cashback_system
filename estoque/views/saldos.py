"""Consulta de posicao de estoque com isolamento por matriz e loja."""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import render
from accounts.services import exigir_permissao
from accounts.permissions import PERMISSAO_ESTOQUE_VISUALIZAR
from core.services import get_contexto_operacional_usuario
from empresas.models import Loja
from estoque.selectors.saldos import get_posicao_estoque, enriquecer_posicao_com_reservas


@login_required
def posicao_estoque(request):
    exigir_permissao(request.user, PERMISSAO_ESTOQUE_VISUALIZAR)
    contexto = get_contexto_operacional_usuario(request.user)
    matriz = contexto['matriz']
    operador = getattr(request.user, 'perfil', None) == getattr(request.user, 'PERFIL_OPERADOR', 'operador')
    lojas = Loja.objects.filter(matriz=matriz).order_by('nome')
    loja_operacional = None
    if operador:
        lojas_usuario = request.user.lojas.filter(matriz=matriz)
        loja_id_sessao = request.session.get('loja_operacional_id')
        if loja_id_sessao is not None:
            loja_operacional = lojas_usuario.filter(pk=loja_id_sessao).first()
        if loja_operacional is None:
            loja_contexto = contexto.get('loja')
            if loja_contexto is not None:
                loja_operacional = lojas_usuario.filter(pk=loja_contexto.pk).first()
        if loja_operacional is None:
            raise PermissionDenied('Operador sem loja operacional autorizada.')
        request.session['loja_operacional_id'] = loja_operacional.pk
        lojas = lojas.filter(pk=loja_operacional.pk)
    busca = request.GET.get('busca', '').strip()[:100]
    loja_id = request.GET.get('loja', '').strip()
    loja_filtro = None
    if not operador and loja_id.isdigit():
        loja_filtro = int(loja_id)
    qs = get_posicao_estoque(matriz=matriz, lojas=lojas, busca=busca, loja_id=loja_filtro)
    pagina = Paginator(qs, 30).get_page(request.GET.get('page'))
    pagina.object_list = enriquecer_posicao_com_reservas(pagina.object_list, matriz=matriz)
    return render(request, 'estoque/posicao.html', {
        'pagina': pagina, 'busca': busca, 'lojas': lojas,
        'loja_id': loja_id if not operador else '',
        'operador': operador, 'loja_operacional': loja_operacional,
    })
