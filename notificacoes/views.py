from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseNotAllowed
from django.shortcuts import render, redirect
from django.utils import timezone

from .models import LeituraAviso
from .selectors import avisos_visiveis_para_usuario, aviso_visivel_para_usuario


@login_required
def lista(request):
    avisos = avisos_visiveis_para_usuario(request.user)
    leituras = set(
        LeituraAviso.objects.filter(
            usuario=request.user, aviso__in=avisos
        ).values_list("aviso_id", flat=True)
    )
    itens = [
        {"aviso": aviso, "lida": aviso.pk in leituras}
        for aviso in avisos
    ]
    return render(request, "notificacoes/lista.html", {"itens": itens})


@login_required
def marcar_lida(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    aviso = aviso_visivel_para_usuario(request.user, pk)
    if aviso is None:
        raise Http404
    LeituraAviso.objects.get_or_create(
        aviso=aviso,
        usuario=request.user,
        defaults={"lido_em": timezone.now()},
    )
    return redirect("notificacoes:lista")
