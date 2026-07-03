function somenteNumeros(valor) {
    return valor.replace(/\D/g, '');
}

function formatarCPF(valor) {
    valor = somenteNumeros(valor).slice(0, 11);

    valor = valor.replace(/(\d{3})(\d)/, '$1.$2');
    valor = valor.replace(/(\d{3})(\d)/, '$1.$2');
    valor = valor.replace(/(\d{3})(\d{1,2})$/, '$1-$2');

    return valor;
}

function formatarTelefone(valor) {
    valor = somenteNumeros(valor).slice(0, 11);

    if (valor.length <= 10) {
        return valor.replace(/(\d{2})(\d{4})(\d{0,4})/, '($1) $2-$3');
    }

    return valor.replace(/(\d{2})(\d{5})(\d{0,4})/, '($1) $2-$3');
}

function formatarData(valor) {
    valor = somenteNumeros(valor).slice(0, 8);

    if (valor.length >= 5) {
        return valor.slice(0, 2) + '/' + valor.slice(2, 4) + '/' + valor.slice(4);
    }

    if (valor.length >= 3) {
        return valor.slice(0, 2) + '/' + valor.slice(2);
    }

    return valor;
}