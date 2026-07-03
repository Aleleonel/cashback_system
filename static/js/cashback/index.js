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

    const valorCompraInput = document.getElementById('id_valor_compra');

    const motorCard = document.getElementById('motor-beneficios-card');
    const mbCashback = document.getElementById('mb-cashback');
    const mbVoucher = document.getElementById('mb-voucher');
    const mbDescontoVoucher = document.getElementById('mb-desconto-voucher');
    const mbCashbackSugerido = document.getElementById('mb-cashback-sugerido');
    const mbValorFinal = document.getElementById('mb-valor-final');

    function esconderMotorBeneficios() {

        if (!motorCard) {
            return;
        }

        motorCard.classList.add('d-none');

        mbCashback.innerText = 'R$ 0,00';
        mbVoucher.innerText = 'Nenhum';
        mbDescontoVoucher.innerText = 'R$ 0,00';
        mbCashbackSugerido.innerText = 'R$ 0,00';
        mbValorFinal.innerText = 'R$ 0,00';
    }

    let saldoAtual = 0;

    function atualizarMotorBeneficios(cpf, valorCompra) {

        if (!motorCard) {
            return;
        }

        if (!valorCompra || Number(valorCompra) <= 0) {
            esconderMotorBeneficios();
            return;
        }

        fetch(`/beneficios/simular/?cpf=${cpf}&valor_compra=${valorCompra}`)

            .then(response => response.json())

            .then(data => {

                if (!data.ok) {
                    esconderMotorBeneficios();
                    return;
                }

                motorCard.classList.remove('d-none');

                mbCashback.innerText =
                    'R$ ' + Number(data.cashback_disponivel).toFixed(2);

                mbVoucher.innerText =
                    data.voucher ? data.voucher.nome : 'Nenhum';

                mbDescontoVoucher.innerText =
                    'R$ ' + Number(data.desconto_voucher).toFixed(2);

                mbCashbackSugerido.innerText =
                    'R$ ' + Number(data.cashback_sugerido).toFixed(2);

                mbValorFinal.innerText =
                    'R$ ' + Number(data.valor_final).toFixed(2);

            })

            .catch(() => {

                esconderMotorBeneficios();

            });

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
            esconderMotorBeneficios();
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

                    if (valorCompraInput.value) {

                        atualizarMotorBeneficios(
                            cpf,
                            valorCompraInput.value
                        );

                    }

                    mostrarStatus(
                        'success',
                        'Cliente encontrado. Dados preenchidos automaticamente.'
                    );
                } else {
                    esconderSaldo();

                    esconderMotorBeneficios();

                    mostrarStatus(
                        'warning',
                        'Cliente não encontrado. Preencha o cadastro rápido.'
                    );
                }
            })
            .catch(() => {
                esconderSaldo();

                esconderMotorBeneficios();

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

    valorCompraInput.addEventListener('input', function () {

        const cpf = somenteNumeros(cpfInput.value);

        if (cpf.length !== 11) {
            esconderMotorBeneficios();
            return;
        }

        atualizarMotorBeneficios(
            cpf,
            valorCompraInput.value
        );

    });
});
