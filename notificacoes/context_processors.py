from .models import LeituraAviso
from .selectors import avisos_visiveis_para_usuario

def notificacoes_navbar(request):
    if not getattr(request.user,"is_authenticated",False):
        return {"notificacoes_nao_lidas":0}
    avisos=avisos_visiveis_para_usuario(request.user)
    lidos=LeituraAviso.objects.filter(usuario=request.user,aviso__in=avisos).values_list("aviso_id",flat=True)
    return {"notificacoes_nao_lidas":avisos.exclude(pk__in=lidos).count()}
