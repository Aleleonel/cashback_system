document.addEventListener('DOMContentLoaded', function () {
    const cpfInput = document.getElementById('id_cpf');
    const nomeInput = document.getElementById('id_nome');
    const telefoneInput = document.getElementById('id_telefone');
    const emailInput = document.getElementById('id_email');
    const nascimentoInput = document.getElementById('id_data_nascimento');
    const cashbackUsadoInput = document.getElementById('id_valor_cashback_usado');
    const valorCompraInput = document.getElementById('id_valor_compra');
    const observacaoInput = document.getElementById('id_observacao');

    const aceitaEmailInput = document.getElementById('id_aceita_email');
    const aceitaSmsInput = document.getElementById('id_aceita_sms');

    const statusBox = document.getElementById('cliente-status');
    const saldoCard = document.getElementById('saldo-card');
    const saldoDisponivel = document.getElementById('saldo-disponivel');
    const usarSaldoTotalBtn = document.getElementById('usar-saldo-total');
    const cancelarCompraBtn = document.getElementById('cancelar-compra');
    const registrarCompraBtn = document.getElementById('registrar-compra');
    const novaCompraForm = document.getElementById('nova-compra-form');

    const motorCard = document.getElementById('motor-beneficios-card');
    const mbCashback = document.getElementById('mb-cashback');
    const mbVoucher = document.getElementById('mb-voucher');
    const mbDescontoVoucher = document.getElementById('mb-desconto-voucher');
    const mbCashbackSugerido = document.getElementById('mb-cashback-sugerido');
    const mbTotalDesconto = document.getElementById('mb-total-desconto');
    const mbValorFinal = document.getElementById('mb-valor-final');

    const codigoVoucherInput = document.getElementById('codigo-voucher');
    const validarVoucherBtn = document.getElementById('validar-voucher-btn');
    const voucherStatus = document.getElementById('voucher-status');
    const voucherInfo = document.getElementById('voucher-info');
    const voucherNome = document.getElementById('voucher-nome');
    const voucherTipo = document.getElementById('voucher-tipo');
    const voucherDesconto = document.getElementById('voucher-desconto');

    const aplicarVoucherInput =
        document.getElementById('aplicar-voucher') ||
        document.getElementById('id_aplicar_voucher');

    const aplicarCashbackInput = document.getElementById('aplicar-cashback');

    let saldoAtual = 0;
    let voucherValidado = null;
    let descontoVoucher = 0;
    let ultimaSimulacao = null;

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
        if (!statusBox) {
            return;
        }

        statusBox.className = 'alert mb-3 alert-' + tipo;
        statusBox.textContent = texto;
        statusBox.classList.remove('d-none');
    }

    function esconderStatus() {
        if (!statusBox) {
            return;
        }

        statusBox.classList.add('d-none');
        statusBox.textContent = '';
    }

    function mostrarSaldo(valor) {
        saldoAtual = parseFloat(valor || 0);

        if (saldoDisponivel) {
            saldoDisponivel.innerText = 'R$ ' + saldoAtual.toFixed(2);
        }

        if (saldoCard) {
            saldoCard.classList.remove('d-none');
        }
    }

    function esconderSaldo() {
        saldoAtual = 0;

        if (saldoDisponivel) {
            saldoDisponivel.innerText = 'R$ 0,00';
        }

        if (saldoCard) {
            saldoCard.classList.add('d-none');
        }
    }

    function limparResumoBeneficios() {
        if (mbCashback) {
            mbCashback.innerText = 'R$ 0,00';
        }

        if (mbVoucher) {
            mbVoucher.innerText = 'Nenhum';
        }

        if (mbDescontoVoucher) {
            mbDescontoVoucher.innerText = 'R$ 0,00';
        }

        if (mbCashbackSugerido) {
            mbCashbackSugerido.innerText = 'R$ 0,00';
        }

        if (mbTotalDesconto) {
            mbTotalDesconto.innerText = 'R$ 0,00';
        }

        if (mbValorFinal) {
            mbValorFinal.innerText = 'R$ 0,00';
        }
    }

    function esconderMotorBeneficios() {
        ultimaSimulacao = null;

        if (motorCard) {
            motorCard.classList.add('d-none');
        }

        limparResumoBeneficios();
    }

    function recalcularResumoBeneficios() {
        const valorCompra = Number(valorCompraInput.value || 0);

        if (!ultimaSimulacao || valorCompra <= 0) {
            limparResumoBeneficios();
            return;
        }

        const aplicarVoucher =
            aplicarVoucherInput &&
            aplicarVoucherInput.checked &&
            voucherValidado;

        const aplicarCashback =
            aplicarCashbackInput &&
            aplicarCashbackInput.checked;

        const descontoVoucherAplicado = aplicarVoucher ? descontoVoucher : 0;

        let cashbackAplicado = 0;

        if (aplicarCashback && cashbackUsadoInput) {
            cashbackAplicado = Number(cashbackUsadoInput.value || 0);
        }

        if (cashbackAplicado > saldoAtual) {
            cashbackAplicado = saldoAtual;

            if (cashbackUsadoInput) {
                cashbackUsadoInput.value = saldoAtual.toFixed(2);
            }

            mostrarStatus(
                'warning',
                'O cashback utilizado não pode ser maior que o saldo disponível.'
            );
        }

        let totalDesconto = descontoVoucherAplicado + cashbackAplicado;

        if (totalDesconto > valorCompra) {
            totalDesconto = valorCompra;
        }

        const valorFinal = valorCompra - totalDesconto;

        if (mbDescontoVoucher) {
            mbDescontoVoucher.innerText =
                'R$ ' + descontoVoucherAplicado.toFixed(2);
        }

        if (mbTotalDesconto) {
            mbTotalDesconto.innerText =
                'R$ ' + totalDesconto.toFixed(2);
        }

        if (mbValorFinal) {
            mbValorFinal.innerText =
                'R$ ' + valorFinal.toFixed(2);
        }
    }

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

                ultimaSimulacao = data;

                motorCard.classList.remove('d-none');

                if (mbCashback) {
                    mbCashback.innerText =
                        'R$ ' + Number(data.cashback_disponivel || 0).toFixed(2);
                }

                if (mbVoucher) {
                    mbVoucher.innerText =
                        data.voucher ? data.voucher.nome : 'Nenhum';
                }

                if (mbCashbackSugerido) {
                    mbCashbackSugerido.innerText =
                        'R$ ' + Number(data.cashback_sugerido || 0).toFixed(2);
                }

                recalcularResumoBeneficios();
            })
            .catch(() => {
                esconderMotorBeneficios();
            });
    }

    function mostrarVoucherStatus(tipo, texto) {
        if (!voucherStatus) {
            return;
        }

        voucherStatus.className = 'alert mt-3 mb-0 alert-' + tipo;
        voucherStatus.textContent = texto;
        voucherStatus.classList.remove('d-none');
    }

    function esconderVoucherStatus() {
        if (!voucherStatus) {
            return;
        }

        voucherStatus.classList.add('d-none');
        voucherStatus.textContent = '';
    }

    function esconderVoucherInfo() {
        voucherValidado = null;
        descontoVoucher = 0;

        if (voucherInfo) {
            voucherInfo.classList.add('d-none');
        }

        if (voucherNome) {
            voucherNome.innerText = '-';
        }

        if (voucherTipo) {
            voucherTipo.innerText = '-';
        }

        if (voucherDesconto) {
            voucherDesconto.innerText = 'R$ 0,00';
        }

        if (aplicarVoucherInput) {
            aplicarVoucherInput.checked = false;
        }

        recalcularResumoBeneficios();
    }

    function validarVoucher() {
        const cpf = somenteNumeros(cpfInput.value);
        const codigo = codigoVoucherInput.value.trim();
        const valorCompra = valorCompraInput.value || '0';

        esconderVoucherInfo();

        if (cpf.length !== 11) {
            mostrarVoucherStatus(
                'warning',
                'Informe um CPF válido antes de validar o voucher.'
            );
            return;
        }

        if (!codigo) {
            mostrarVoucherStatus(
                'warning',
                'Informe o código do voucher.'
            );
            return;
        }

        if (!valorCompra || Number(valorCompra) <= 0) {
            mostrarVoucherStatus(
                'warning',
                'Informe o valor da compra antes de validar o voucher.'
            );
            return;
        }

        fetch(
            `/beneficios/validar-voucher/?cpf=${cpf}&codigo=${encodeURIComponent(codigo)}&valor_compra=${valorCompra}`
        )
            .then(response => response.json())
            .then(data => {
                if (!data.ok) {
                    mostrarVoucherStatus(
                        'danger',
                        data.mensagem || 'Voucher inválido.'
                    );
                    return;
                }

                voucherValidado = data;
                descontoVoucher = Number(data.desconto || 0);

                mostrarVoucherStatus(
                    'success',
                    data.mensagem || 'Voucher válido.'
                );

                if (voucherInfo) {
                    voucherInfo.classList.remove('d-none');
                }

                if (voucherNome) {
                    voucherNome.innerText = data.nome || '-';
                }

                if (voucherTipo) {
                    voucherTipo.innerText = data.tipo || '-';
                }

                if (voucherDesconto) {
                    voucherDesconto.innerText =
                        'R$ ' + descontoVoucher.toFixed(2);
                }

                recalcularResumoBeneficios();
            })
            .catch(() => {
                mostrarVoucherStatus(
                    'danger',
                    'Erro ao validar voucher. Tente novamente.'
                );
            });
    }

    function criarModalOperacao() {
        let modal = document.getElementById('modal-operacao-caixa');

        if (modal) {
            return modal;
        }

        modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'modal-operacao-caixa';
        modal.tabIndex = -1;
        modal.setAttribute('aria-hidden', 'true');

        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">

                    <div class="modal-header">
                        <h5 class="modal-title" id="modal-operacao-titulo">
                            Confirmar operação
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Fechar"></button>
                    </div>

                    <div class="modal-body">
                        <p class="mb-0" id="modal-operacao-mensagem"></p>
                    </div>

                    <div class="modal-footer">
                        <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">
                            Voltar
                        </button>

                        <button type="button" class="btn btn-dark" id="modal-operacao-confirmar">
                            Confirmar
                        </button>
                    </div>

                </div>
            </div>
        `;

        document.body.appendChild(modal);

        return modal;
    }

    function confirmarOperacao({ titulo, mensagem, textoConfirmar, classeConfirmar, aoConfirmar }) {
        const modalElement = criarModalOperacao();

        const tituloElement = modalElement.querySelector('#modal-operacao-titulo');
        const mensagemElement = modalElement.querySelector('#modal-operacao-mensagem');
        let confirmarBtn = modalElement.querySelector('#modal-operacao-confirmar');

        tituloElement.textContent = titulo;
        mensagemElement.textContent = mensagem;
        confirmarBtn.textContent = textoConfirmar || 'Confirmar';
        confirmarBtn.className = classeConfirmar || 'btn btn-dark';

        const novoConfirmarBtn = confirmarBtn.cloneNode(true);
        confirmarBtn.parentNode.replaceChild(novoConfirmarBtn, confirmarBtn);
        confirmarBtn = novoConfirmarBtn;

        if (window.bootstrap && window.bootstrap.Modal) {
            const modalBootstrap = window.bootstrap.Modal.getOrCreateInstance(modalElement);

            confirmarBtn.addEventListener('click', function () {
                modalBootstrap.hide();
                aoConfirmar();
            });

            modalBootstrap.show();
            return;
        }

        if (confirm(mensagem)) {
            aoConfirmar();
        }
    }

    function calcularValorCashbackParaUsar() {
        if (!ultimaSimulacao) {
            return saldoAtual;
        }

        const sugerido = Number(ultimaSimulacao.cashback_sugerido || 0);

        if (sugerido > 0) {
            return Math.min(saldoAtual, sugerido);
        }

        return saldoAtual;
    }

    function cancelarCompra() {
        confirmarOperacao({
            titulo: 'Cancelar operação',
            mensagem: 'Deseja realmente cancelar esta compra? Todos os dados preenchidos serão descartados.',
            textoConfirmar: 'Cancelar compra',
            classeConfirmar: 'btn btn-danger',
            aoConfirmar: function () {
                if (cpfInput) {
                    cpfInput.value = '';
                }

                if (nomeInput) {
                    nomeInput.value = '';
                }

                if (telefoneInput) {
                    telefoneInput.value = '';
                }

                if (emailInput) {
                    emailInput.value = '';
                }

                if (nascimentoInput) {
                    nascimentoInput.value = '';
                }

                if (valorCompraInput) {
                    valorCompraInput.value = '';
                }

                if (cashbackUsadoInput) {
                    cashbackUsadoInput.value = '';
                }

                if (codigoVoucherInput) {
                    codigoVoucherInput.value = '';
                }

                if (observacaoInput) {
                    observacaoInput.value = '';
                }

                if (aceitaEmailInput) {
                    aceitaEmailInput.checked = true;
                }

                if (aceitaSmsInput) {
                    aceitaSmsInput.checked = false;
                }

                if (aplicarVoucherInput) {
                    aplicarVoucherInput.checked = false;
                }

                if (aplicarCashbackInput) {
                    aplicarCashbackInput.checked = false;
                }

                saldoAtual = 0;
                voucherValidado = null;
                descontoVoucher = 0;
                ultimaSimulacao = null;

                esconderStatus();
                esconderSaldo();
                esconderMotorBeneficios();
                esconderVoucherInfo();
                esconderVoucherStatus();
                limparResumoBeneficios();

                mostrarStatus(
                    'secondary',
                    'Operação cancelada. Inicie uma nova compra.'
                );

                if (cpfInput) {
                    cpfInput.focus();
                }
            }
        });
    }

    if (usarSaldoTotalBtn) {
        usarSaldoTotalBtn.addEventListener('click', function () {
            const valorCashbackParaUsar = calcularValorCashbackParaUsar();

            if (saldoAtual <= 0 || valorCashbackParaUsar <= 0) {
                mostrarStatus(
                    'warning',
                    'Este cliente não possui cashback disponível para uso nesta compra.'
                );
                return;
            }

            const valorFormatado = valorCashbackParaUsar.toFixed(2).replace('.', ',');

            confirmarOperacao({
                titulo: 'Aplicar cashback',
                mensagem: `Será aplicado R$ ${valorFormatado} de cashback nesta compra. Voucher e cashback não podem ser usados juntos.`,
                textoConfirmar: 'Aplicar cashback',
                classeConfirmar: 'btn btn-success',
                aoConfirmar: function () {
                    if (aplicarVoucherInput) {
                        aplicarVoucherInput.checked = false;
                    }

                    if (aplicarCashbackInput) {
                        aplicarCashbackInput.checked = true;
                    }

                    cashbackUsadoInput.value = valorCashbackParaUsar.toFixed(2);

                    mostrarStatus(
                        'success',
                        `Cashback de R$ ${valorFormatado} aplicado nesta compra.`
                    );

                    recalcularResumoBeneficios();
                }
            });
        });
    }

    cpfInput.addEventListener('input', function () {
        cpfInput.value = formatarCPF(cpfInput.value);
        esconderVoucherInfo();
        esconderVoucherStatus();
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
            esconderVoucherInfo();
            esconderVoucherStatus();
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

                    if (aceitaEmailInput) {
                        aceitaEmailInput.checked = Boolean(data.aceita_email);
                    }

                    if (aceitaSmsInput) {
                        aceitaSmsInput.checked = Boolean(data.aceita_sms);
                    }

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
                    esconderVoucherInfo();
                    esconderVoucherStatus();

                    mostrarStatus(
                        'warning',
                        'Cliente não encontrado. Preencha o cadastro rápido.'
                    );
                }
            })
            .catch(() => {
                esconderSaldo();
                esconderMotorBeneficios();
                esconderVoucherInfo();
                esconderVoucherStatus();

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

        if (aplicarCashbackInput) {
            aplicarCashbackInput.checked = valorDigitado > 0;
        }

        if (valorDigitado > 0 && aplicarVoucherInput) {
            aplicarVoucherInput.checked = false;
        }

        recalcularResumoBeneficios();
    });

    valorCompraInput.addEventListener('input', function () {
        const cpf = somenteNumeros(cpfInput.value);

        esconderVoucherInfo();
        esconderVoucherStatus();

        if (cpf.length !== 11) {
            esconderMotorBeneficios();
            return;
        }

        atualizarMotorBeneficios(
            cpf,
            valorCompraInput.value
        );
    });

    if (validarVoucherBtn) {
        validarVoucherBtn.addEventListener('click', function () {
            validarVoucher();
        });
    }

    if (codigoVoucherInput) {
        codigoVoucherInput.addEventListener('input', function () {
            esconderVoucherInfo();
            esconderVoucherStatus();
        });
    }

    if (aplicarVoucherInput) {
        aplicarVoucherInput.addEventListener('change', function () {
            if (this.checked) {
                if (aplicarCashbackInput) {
                    aplicarCashbackInput.checked = false;
                }

                if (cashbackUsadoInput) {
                    cashbackUsadoInput.value = '';
                }
            }

            recalcularResumoBeneficios();
        });
    }

    if (aplicarCashbackInput) {
        aplicarCashbackInput.addEventListener('change', function () {
            if (this.checked) {
                if (aplicarVoucherInput) {
                    aplicarVoucherInput.checked = false;
                }
            }

            recalcularResumoBeneficios();
        });
    }

    if (cancelarCompraBtn) {
        cancelarCompraBtn.addEventListener('click', function () {
            cancelarCompra();
        });
    }

    if (novaCompraForm && registrarCompraBtn) {
        let envioEmAndamento = false;

        novaCompraForm.addEventListener('submit', function (event) {
            if (envioEmAndamento) {
                event.preventDefault();
                return;
            }

            envioEmAndamento = true;
            registrarCompraBtn.disabled = true;
            registrarCompraBtn.textContent = 'Registrando...';
        });
    }
});
