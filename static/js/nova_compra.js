document.addEventListener('DOMContentLoaded', function () {
    const cpfInput = document.getElementById('id_cpf');
    const nomeInput = document.getElementById('id_nome');
    const telefoneInput = document.getElementById('id_telefone');
    const emailInput = document.getElementById('id_email');
    const nascimentoInput = document.getElementById('id_data_nascimento');
    const cashbackUsadoInput = document.getElementById('id_valor_cashback_usado');

    const statusBox = document.getElementById('cliente-status');
    const saldoCard = document.getElementById('saldo-card');
    const saldoDisponivel = document.getElementById('saldo-disponivel');
    const usarSaldoTotalBtn = document.getElementById('usar-saldo-total');

    let saldoAtual = 0;

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

    function mostrarStatus(tipo, texto) {
        statusBox.className = 'alert mb-3 alert-' + tipo;
        statusBox.textContent = texto;
        statusBox.classList.remove('d-none');
    }

    function esconderStatus() {
        statusBox.classList.add('d-none');
        statusBox.textContent = '';
    }

    function mostrarSaldo(valor) {
        saldoAtual = parseFloat(valor || 0);
        saldoDisponivel.innerText = 'R$ ' + saldoAtual.toFixed(2);
        saldoCard.classList.remove('d-none');
    }

    function esconderSaldo() {
        saldoAtual = 0;
        saldoDisponivel.innerText = 'R$ 0,00';
        saldoCard.classList.add('d-none');
    }
    if (usarSaldoTotalBtn) {
        usarSaldoTotalBtn.addEventListener('click', function () {
            if (saldoAtual <= 0) {
                mostrarStatus(
                    'warning',
                    'Este cliente não possui cashback disponível para uso.'
                );
                return;
            }

            const valorFormatado = saldoAtual.toFixed(2).replace('.', ',');

            const confirmar = confirm(
                `Deseja realmente usar R$ ${valorFormatado} de cashback nesta compra?`
            );

            if (confirmar) {
                cashbackUsadoInput.value = saldoAtual.toFixed(2);

                mostrarStatus(
                    'success',
                    `Cashback de R$ ${valorFormatado} aplicado nesta compra.`
                );
            }
        });
    }

    cpfInput.addEventListener('input', function () {
        cpfInput.value = formatarCPF(cpfInput.value);
    });

    telefoneInput.addEventListener('input', function () {
        telefoneInput.value = formatarTelefone(telefoneInput.value);
    });

    nascimentoInput.addEventListener('input', function () {
        nascimentoInput.value = formatarData(nascimentoInput.value);
    });

    cpfInput.addEventListener('blur', function () {
        const cpf = somenteNumeros(cpfInput.value);

        if (cpf.length < 11) {
            esconderStatus();
            esconderSaldo();
            return;
        }

        fetch(`/clientes/buscar-cpf/?cpf=${cpf}`)
            .then(response => response.json())
            .then(data => {
                if (data.encontrado) {
                    nomeInput.value = data.nome || '';
                    telefoneInput.value = formatarTelefone(data.telefone || '');
                    emailInput.value = data.email || '';
                    nascimentoInput.value = data.data_nascimento || '';

                    mostrarSaldo(data.saldo_disponivel);

                    mostrarStatus(
                        'success',
                        'Cliente encontrado. Dados preenchidos automaticamente.'
                    );
                } else {
                    esconderSaldo();

                    mostrarStatus(
                        'warning',
                        'Cliente não encontrado. Preencha o cadastro rápido.'
                    );
                }
            })
            .catch(() => {
                esconderSaldo();

                mostrarStatus(
                    'danger',
                    'Erro ao buscar cliente. Tente novamente.'
                );
            });
    });

    cashbackUsadoInput.addEventListener('input', function () {
        const valorDigitado = parseFloat(cashbackUsadoInput.value || 0);

        if (valorDigitado > saldoAtual) {
            cashbackUsadoInput.value = saldoAtual.toFixed(2);

            mostrarStatus(
                'warning',
                'O cashback utilizado não pode ser maior que o saldo disponível.'
            );
        }
    });
});
