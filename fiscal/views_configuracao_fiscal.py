from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render

from accounts.decorators import require_permission
from core.services import get_contexto_operacional_usuario
from fiscal.constants import PERMISSAO_FISCAL_CONFIGURAR
from fiscal.forms_configuracao_fiscal import ConfiguracaoFiscalMatrizForm
from fiscal.selectors_configuracao_fiscal import (
    get_configuracao_fiscal_matriz_para_edicao,
)
from fiscal.services_configuracao_fiscal import (
    atualizar_configuracao_fiscal_matriz,
    criar_configuracao_fiscal_matriz,
)


def _aplicar_erros_no_form(*, form, erro):
    if hasattr(erro, "message_dict"):
        for campo, mensagens in erro.message_dict.items():
            for mensagem in mensagens:
                form.add_error(
                    campo if campo in form.fields else None,
                    mensagem,
                )
        return

    for mensagem in erro.messages:
        form.add_error(None, mensagem)


@login_required
@require_permission(PERMISSAO_FISCAL_CONFIGURAR)
def configuracao_fiscal_matriz_view(request):
    contexto = get_contexto_operacional_usuario(request.user)
    matriz = contexto.get("matriz")
    loja = contexto.get("loja")

    if matriz is None:
        messages.error(
            request,
            "Nao foi possivel identificar a matriz do contexto operacional.",
        )
        return redirect("fiscal:inicio")

    configuracao = get_configuracao_fiscal_matriz_para_edicao(
        matriz=matriz,
    )

    if request.method == "POST":
        form = ConfiguracaoFiscalMatrizForm(
            request.POST,
            instance=configuracao,
        )

        if form.is_valid():
            try:
                if configuracao is None:
                    configuracao = criar_configuracao_fiscal_matriz(
                        matriz=matriz,
                        dados=form.cleaned_data,
                        usuario_executor=request.user,
                        loja=loja,
                        request=request,
                    )
                    mensagem = (
                        "Configuracao fiscal da matriz criada com sucesso."
                    )
                else:
                    configuracao = atualizar_configuracao_fiscal_matriz(
                        configuracao=configuracao,
                        dados=form.cleaned_data,
                        usuario_executor=request.user,
                        loja=loja,
                        request=request,
                    )
                    mensagem = (
                        "Configuracao fiscal da matriz atualizada com sucesso."
                    )
            except ValidationError as erro:
                _aplicar_erros_no_form(
                    form=form,
                    erro=erro,
                )
            else:
                messages.success(request, mensagem)
                return redirect(
                    "fiscal:configuracao_fiscal_matriz"
                )
    else:
        form = ConfiguracaoFiscalMatrizForm(
            instance=configuracao,
        )

    return render(
        request,
        "fiscal/configuracao_fiscal_matriz/form.html",
        {
            "form": form,
            "matriz": matriz,
            "loja": loja,
            "configuracao": configuracao,
            "configurada": configuracao is not None,
            "pronta_para_operacao": (
                configuracao.pronta_para_operacao
                if configuracao is not None
                else False
            ),
        },
    )
