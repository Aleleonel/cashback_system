function aplicarVariaveisTemplateCampanha(texto) {
    const variaveis = {
        '{nome}': 'Alexandre',
        '{saldo}': '25,00',
        '{dias}': '7',
        '{loja}': 'Pro Corps',
        '{email}': 'cliente@email.com',
        '{telefone}': '11999999999'
    };

    let resultado = texto || '';

    Object.keys(variaveis).forEach(function (chave) {
        resultado = resultado.replaceAll(chave, variaveis[chave]);
    });

    return resultado;
}

function atualizarPreviewTemplateCampanha() {
    const assuntoInput = document.getElementById('id_assunto');
    const mensagemInput = document.getElementById('id_mensagem');

    const previewAssunto = document.getElementById('preview-assunto');
    const previewMensagem = document.getElementById('preview-mensagem');

    if (!assuntoInput || !mensagemInput || !previewAssunto || !previewMensagem) {
        return;
    }

    const assunto = aplicarVariaveisTemplateCampanha(assuntoInput.value);
    const mensagem = aplicarVariaveisTemplateCampanha(mensagemInput.value);

    previewAssunto.textContent = assunto || '-';
    previewMensagem.innerHTML = (mensagem || '-').replace(/\n/g, '<br>');
}

document.addEventListener('DOMContentLoaded', function () {
    const assuntoInput = document.getElementById('id_assunto');
    const mensagemInput = document.getElementById('id_mensagem');

    if (assuntoInput) {
        assuntoInput.addEventListener('input', atualizarPreviewTemplateCampanha);
    }

    if (mensagemInput) {
        mensagemInput.addEventListener('input', atualizarPreviewTemplateCampanha);
    }

    atualizarPreviewTemplateCampanha();
});