from django.shortcuts import render, redirect
from configuracoes.decorators import central_configuracoes_required
from notificacoes.forms import AvisoInternoForm
from notificacoes.models import AvisoInterno

@central_configuracoes_required
def notificacoes(request):
    ctx=request.contexto_configuracoes
    matriz=getattr(ctx,"matriz",None) if not isinstance(ctx,dict) else ctx.get("matriz")
    qs=AvisoInterno.objects.filter(matriz=matriz).select_related("loja","criado_por").order_by("-inicio_exibicao") if matriz else AvisoInterno.objects.none()
    return render(request,"configuracoes/notificacoes.html",{"avisos":qs,"matriz":matriz})

@central_configuracoes_required
def notificacoes_novo(request):
    ctx=request.contexto_configuracoes
    matriz=getattr(ctx,"matriz",None) if not isinstance(ctx,dict) else ctx.get("matriz")
    if matriz is None:
        return render(request,"configuracoes/notificacoes_form.html",{"sem_matriz":True},status=400)
    form=AvisoInternoForm(request.POST or None,matriz=matriz)
    if request.method=="POST" and form.is_valid():
        aviso=form.save(commit=False);aviso.matriz=matriz;aviso.criado_por=request.user;aviso.save()
        return redirect("configuracoes:notificacoes")
    return render(request,"configuracoes/notificacoes_form.html",{"form":form,"matriz":matriz})
