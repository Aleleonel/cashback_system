function marcarCanalTemplate(canal) {
    const emailInput = document.getElementById('id_enviar_email');
    const whatsappInput = document.getElementById('id_enviar_whatsapp');
    const smsInput = document.getElementById('id_enviar_sms');

    if (emailInput) {
        emailInput.checked = canal === 'email';
    }

    if (whatsappInput) {
        whatsappInput.checked = canal === 'whatsapp';
    }

    if (smsInput) {
        smsInput.checked = canal === 'sms';
    }
}

async function buscarTemplateSelecionado(templateId) {
    const config = document.getElementById('template-json-config');

    if (!config || !templateId) {
        return null;
    }

    const urlTemplate = config.dataset.url;
    const placeholder = config.dataset.placeholder;

    if (!urlTemplate || !placeholder) {
        return null;
    }

    const url = urlTemplate.replace(
        placeholder,
        templateId
    );

    const response = await fetch(url, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    });

    if (!response.ok) {
        return null;
    }

    return await response.json();
}

async function aplicarTemplateSelecionado() {
    const templateSelect = document.getElementById('id_template');
    const assuntoInput = document.getElementById('id_assunto');
    const mensagemInput = document.getElementById('id_mensagem');

    if (!templateSelect || !assuntoInput || !mensagemInput) {
        return;
    }

    const templateId = templateSelect.value;

    if (!templateId) {
        return;
    }

    const template = await buscarTemplateSelecionado(templateId);

    if (!template) {
        return;
    }

    assuntoInput.value = template.assunto || '';
    mensagemInput.value = template.mensagem || '';

    marcarCanalTemplate(template.canal);
}

document.addEventListener('DOMContentLoaded', function () {
    const templateSelect = document.getElementById('id_template');

    if (!templateSelect) {
        return;
    }

    templateSelect.addEventListener('change', aplicarTemplateSelecionado);
});