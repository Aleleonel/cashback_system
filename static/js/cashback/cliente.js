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