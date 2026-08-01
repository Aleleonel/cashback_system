(() => {
    "use strict";

    const app = document.getElementById("pdv-app");
    if (!app) return;

    const busca = document.getElementById("pdv-busca");
    const formBusca = document.getElementById("pdv-form-busca");
    const resultados = document.getElementById("pdv-resultados");
    const corpoItens = document.getElementById("pdv-itens");
    const formCliente = document.getElementById("pdv-form-cliente");
    const buscaCliente = document.getElementById("pdv-busca-cliente");
    const resultadosClientes = document.getElementById("pdv-resultados-clientes");
    const clienteNome = document.getElementById("pdv-cliente-nome");
    const clienteDocumento = document.getElementById("pdv-cliente-documento");
    const vendedorSelect = document.getElementById("pdv-vendedor");
    const vendedorAtual = document.getElementById("pdv-vendedor-atual");
    const clienteNomePadrao = clienteNome?.textContent.trim() || "CONSUMIDOR";
    const clienteDocumentoPadrao =
        clienteDocumento?.textContent.trim() || "Cliente padrão da matriz";
    const vendedorAtualPadrao = vendedorAtual?.textContent.trim() || "";
    const cashbackDisponivel = document.getElementById("pdv-cashback-disponivel");
    const voucherRecomendado = document.getElementById("pdv-voucher-recomendado");
    const descontoRecomendado = document.getElementById("pdv-desconto-recomendado");
    const cashbackPrevisto = document.getElementById("pdv-cashback-previsto");
    const vazio = document.getElementById("pdv-vazio");
    const alerta = document.getElementById("pdv-alerta");
    const botaoFinalizar = document.getElementById("pdv-finalizar");
    const caixaAberto = app.dataset.caixaAberto === "true";
    let vendaAtual = null;
    let formasPagamento = [];
    let modalFechamento = null;
    let voucherAplicado = null;

    const csrfToken = () => {
        const input = document.querySelector(
            'input[name="csrfmiddlewaretoken"]'
        );

        const tokenDoHtml = input?.value?.trim() || "";

        if (tokenDoHtml.length === 32 || tokenDoHtml.length === 64) {
            return tokenDoHtml;
        }

        const prefixo = "csrftoken=";
        const cookie = document.cookie
            .split(";")
            .map((item) => item.trim())
            .find((item) => item.startsWith(prefixo));

        const tokenDoCookie = cookie
            ? decodeURIComponent(cookie.substring(prefixo.length)).trim()
            : "";

        if (tokenDoCookie.length === 32 || tokenDoCookie.length === 64) {
            return tokenDoCookie;
        }

        console.error("Token CSRF ausente ou inválido", {
            tamanhoHtml: tokenDoHtml.length,
            tamanhoCookie: tokenDoCookie.length,
        });

        throw new Error(
            "Token de segurança CSRF ausente ou inválido. Atualize a página."
        );
    };

    const moeda = (valor) =>
        new Intl.NumberFormat("pt-BR", {
            style: "currency",
            currency: "BRL",
        }).format(Number(valor || 0));

    const escapar = (valor) => {
        const div = document.createElement("div");
        div.textContent = valor == null ? "" : String(valor);
        return div.innerHTML;
    };

    const mostrarAlerta = (mensagem, tipo = "danger") => {
        alerta.className = `alert alert-${tipo}`;
        alerta.textContent = mensagem;
        alerta.classList.remove("d-none");
    };

    const limparAlerta = () => {
        alerta.classList.add("d-none");
        alerta.textContent = "";
    };

    const lerJsonSeguro = async (resposta, url) => {
        const contentType = resposta.headers.get("content-type") || "";
        const texto = await resposta.text();

        if (!contentType.includes("application/json")) {
            console.error("PDV recebeu resposta não JSON", {
                url,
                status: resposta.status,
                statusText: resposta.statusText,
                contentType,
                respostaInicial: texto.slice(0, 2000),
            });

            throw new Error(
                `Resposta inválida do servidor. URL: ${url} | ` +
                `Status: ${resposta.status} ${resposta.statusText}.`
            );
        }

        try {
            return JSON.parse(texto);
        } catch (erro) {
            console.error("PDV recebeu JSON inválido", {
                url,
                status: resposta.status,
                contentType,
                respostaInicial: texto.slice(0, 2000),
                erro,
            });

            throw new Error(
                `JSON inválido recebido do servidor. URL: ${url} | ` +
                `Status: ${resposta.status} ${resposta.statusText}.`
            );
        }
    };

    const post = async (url, dados) => {
        const resposta = await fetch(url, {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken(),
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            },
            body: new URLSearchParams(dados),
        });

        const payload = await lerJsonSeguro(resposta, url);

        if (!resposta.ok || !payload.ok) {
            throw new Error(
                payload.erro || "Não foi possível concluir a operação."
            );
        }

        return payload;
    };


    const postJson = async (url, dados) => {
        const resposta = await fetch(url, {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken(),
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/json;charset=UTF-8",
            },
            body: JSON.stringify(dados),
        });
        const payload = await lerJsonSeguro(resposta, url);
        if (!resposta.ok || !payload.ok) {
            throw new Error(payload.erro || "Nao foi possivel concluir a operacao.");
        }
        return payload;
    };

    const urlItem = (base, id) => base.replace("/0/", `/${id}/`);

    const renderVenda = (venda) => {
        vendaAtual = venda;
        const itens = venda.itens || [];
        corpoItens.innerHTML = itens
            .map(
                (item) => `
                <tr data-item-id="${item.id}">
                    <td>
                        <div class="fw-semibold">${escapar(item.produto)}</div>
                        <div class="text-muted small">${escapar(item.codigo)}</div>
                    </td>
                    <td class="text-end">
                        <input class="form-control form-control-sm text-end pdv-quantidade"
                            type="number" min="0.001" step="0.001"
                            value="${escapar(item.quantidade)}">
                    </td>
                    <td class="text-end">${moeda(item.preco_unitario)}</td>
                    <td class="text-end">
                        <input class="form-control form-control-sm text-end pdv-desconto-item"
                            type="number" min="0" step="0.01"
                            value="${escapar(item.desconto)}">
                    </td>
                    <td class="text-end fw-semibold">${moeda(item.total)}</td>
                    <td class="text-end">
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary pdv-salvar-item" type="button">
                                Salvar
                            </button>
                            <button class="btn btn-outline-danger pdv-remover-item" type="button">
                                Remover
                            </button>
                        </div>
                    </td>
                </tr>`
            )
            .join("");

        vazio.classList.toggle("d-none", itens.length > 0);
        document.getElementById("pdv-contagem").textContent =
            `${itens.length} ${itens.length === 1 ? "item" : "itens"}`;
        document.getElementById("pdv-subtotal").textContent = moeda(venda.subtotal);
        document.getElementById("pdv-desconto").textContent = moeda(venda.desconto);
        document.getElementById("pdv-acrescimo").textContent = moeda(venda.acrescimo);
        document.getElementById("pdv-total").textContent = moeda(venda.total);
        const statusVenda = document.getElementById("pdv-status-venda");
        statusVenda.textContent = venda.id
            ? `${venda.status_display || "Venda em andamento"} #${venda.id}`
            : "Nova venda";

        if (botaoFinalizar) {
            const finalizada = venda.status === "finalizada";
            botaoFinalizar.disabled =
                !caixaAberto || !venda.id || itens.length === 0 || finalizada;
            botaoFinalizar.classList.toggle("btn-success", finalizada);
            botaoFinalizar.classList.toggle("btn-primary", !finalizada);
            botaoFinalizar.innerHTML = finalizada
                ? '<i class="bi bi-check-circle-fill me-1"></i>Venda finalizada'
                : '<i class="bi bi-check-circle me-1"></i>Finalizar venda ' +
                  '<span class="ms-1 opacity-75">F6</span>';
        }

        if (venda.cliente) {
            clienteNome.textContent = venda.cliente.nome;
            clienteDocumento.textContent =
                venda.cliente.cpf || venda.cliente.telefone || "Cliente identificado";
        } else {
            clienteNome.textContent = clienteNomePadrao;
            clienteDocumento.textContent = clienteDocumentoPadrao;
        }

        if (venda.vendedor) {
            vendedorAtual.textContent = venda.vendedor.nome;
            if (vendedorSelect.querySelector(`option[value="${venda.vendedor.id}"]`)) {
                vendedorSelect.value = String(venda.vendedor.id);
            }
        } else {
            vendedorAtual.textContent = vendedorAtualPadrao;
            vendedorSelect.value = "";
            vendedorSelect.selectedIndex = -1;
        }

        const beneficios = venda.beneficios || {};
        cashbackDisponivel.textContent = moeda(
            beneficios.cashback_disponivel || "0.00"
        );
        descontoRecomendado.textContent = moeda(
            beneficios.desconto_recomendado || "0.00"
        );
        cashbackPrevisto.textContent = moeda(
            beneficios.cashback_previsto || "0.00"
        );

        if (beneficios.voucher_recomendado) {
            voucherRecomendado.textContent =
                `${beneficios.voucher_recomendado.codigo} — ` +
                `${beneficios.voucher_recomendado.nome}`;
            voucherRecomendado.title =
                `Validade: ${beneficios.voucher_recomendado.data_fim}`;
        } else {
            voucherRecomendado.textContent = "Nenhum";
            voucherRecomendado.removeAttribute("title");
        }
    };

    const carregarEstado = async () => {
        try {
            const url = app.dataset.estadoUrl;
            const resposta = await fetch(url, {
                headers: { "X-Requested-With": "XMLHttpRequest" },
            });

            const payload = await lerJsonSeguro(resposta, url);

            if (!resposta.ok || !payload.ok) {
                throw new Error(
                    payload.erro || "Não foi possível carregar o estado da venda."
                );
            }

            renderVenda(payload.venda);
        } catch (erro) {
            mostrarAlerta(erro.message);
        }
    };

    const pesquisarClientes = async () => {
        limparAlerta();
        resultadosClientes.innerHTML = "";
        const termo = buscaCliente.value.trim();

        if (termo.length < 2) {
            mostrarAlerta("Digite pelo menos 2 caracteres para localizar o cliente.", "warning");
            return;
        }

        try {
            const url = `${app.dataset.buscaClientesUrl}?q=${encodeURIComponent(termo)}`;
            const resposta = await fetch(url, {
                headers: { "X-Requested-With": "XMLHttpRequest" },
            });
            const payload = await lerJsonSeguro(resposta, url);
            if (!resposta.ok || !payload.ok) {
                throw new Error(payload.erro || "Falha ao pesquisar clientes.");
            }

            if (!payload.clientes.length) {
                resultadosClientes.innerHTML =
                    '<div class="border rounded-3 p-3 text-center text-muted small">Nenhum cliente encontrado.</div>';
                return;
            }

            resultadosClientes.innerHTML = payload.clientes.map((cliente) => `
                <button class="pdv-product-result" type="button" data-cliente-id="${cliente.id}">
                    <span><strong>${escapar(cliente.nome)}</strong><small>${escapar(cliente.cpf || "Sem CPF")}</small></span>
                    <span class="text-end"><small>${escapar(cliente.telefone || cliente.email || "")}</small></span>
                </button>
            `).join("");
        } catch (erro) {
            mostrarAlerta(erro.message);
        }
    };

    const carregarVendedores = async () => {
        try {
            const url = app.dataset.buscaVendedoresUrl;
            const resposta = await fetch(url, {
                headers: { "X-Requested-With": "XMLHttpRequest" },
            });
            const payload = await lerJsonSeguro(resposta, url);
            if (!resposta.ok || !payload.ok) {
                throw new Error(payload.erro || "Falha ao carregar vendedores.");
            }

            vendedorSelect.innerHTML = payload.vendedores.map((vendedor) =>
                `<option value="${vendedor.id}">${escapar(vendedor.nome)}</option>`
            ).join("");
        } catch (erro) {
            vendedorSelect.innerHTML = '<option value="">Vendedores indisponíveis</option>';
            mostrarAlerta(erro.message);
        }
    };

    const pesquisar = async () => {
        limparAlerta();
        const termo = busca.value.trim();
        resultados.innerHTML = "";

        if (termo.length < 2) {
            mostrarAlerta(
                "Digite pelo menos 2 caracteres para pesquisar.",
                "warning"
            );
            return;
        }

        try {
            const url = `${app.dataset.buscaUrl}?q=${encodeURIComponent(termo)}`;
            const resposta = await fetch(url, {
                headers: { "X-Requested-With": "XMLHttpRequest" },
            });

            const payload = await lerJsonSeguro(resposta, url);

            if (!resposta.ok || !payload.ok) {
                mostrarAlerta(
                    payload.erro || "Falha ao pesquisar produtos."
                );
                return;
            }

            if (!payload.produtos.length) {
                resultados.innerHTML =
                    '<div class="pdv-product-empty border rounded-3 p-4 text-center">' +
                    '<i class="bi bi-box-seam fs-2 text-muted"></i>' +
                    '<div class="fw-semibold mt-2">Nenhum produto encontrado</div></div>';
                return;
            }

            resultados.innerHTML = payload.produtos
                .map(
                    (produto) => `
                    <button class="pdv-product-result" type="button"
                        data-produto-id="${produto.id}">
                        <span>
                            <strong>${escapar(produto.nome)}</strong>
                            <small>${escapar(produto.codigo)}${produto.gtin ? ` · ${escapar(produto.gtin)}` : ""}</small>
                        </span>
                        <span class="text-end">
                            <strong>${moeda(produto.preco)}</strong>
                            <small>${produto.controla_estoque ? "Controla estoque" : "Sem controle de estoque"}</small>
                        </span>
                    </button>`
                )
                .join("");
        } catch (erro) {
            mostrarAlerta(erro.message);
        }
    };

    formCliente?.addEventListener("submit", (evento) => {
        evento.preventDefault();
        pesquisarClientes();
    });

    resultadosClientes?.addEventListener("click", async (evento) => {
        const botao = evento.target.closest("[data-cliente-id]");
        if (!botao) return;
        try {
            const payload = await post(app.dataset.selecionarClienteUrl, {
                cliente_id: botao.dataset.clienteId,
            });
            renderVenda(payload.venda);
            resultadosClientes.innerHTML = "";
            buscaCliente.value = "";
            mostrarAlerta("Cliente selecionado.", "success");
        } catch (erro) {
            mostrarAlerta(erro.message);
        }
    });

    vendedorSelect?.addEventListener("change", async () => {
        if (!vendedorSelect.value) return;
        try {
            const payload = await post(app.dataset.selecionarVendedorUrl, {
                vendedor_id: vendedorSelect.value,
            });
            renderVenda(payload.venda);
            mostrarAlerta("Vendedor selecionado.", "success");
        } catch (erro) {
            mostrarAlerta(erro.message);
        }
    });

    formBusca.addEventListener("submit", (evento) => {
        evento.preventDefault();
        pesquisar();
    });

    resultados.addEventListener("click", async (evento) => {
        const botao = evento.target.closest("[data-produto-id]");
        if (!botao) return;

        limparAlerta();
        botao.disabled = true;

        try {
            const payload = await post(app.dataset.adicionarUrl, {
                produto_id: botao.dataset.produtoId,
                quantidade: "1.000",
            });

            renderVenda(payload.venda);
            resultados.innerHTML = "";
            busca.value = "";
            busca.focus();
            mostrarAlerta("Produto adicionado à venda.", "success");
        } catch (erro) {
            mostrarAlerta(erro.message);
        } finally {
            botao.disabled = false;
        }
    });

    corpoItens.addEventListener("click", async (evento) => {
        const linha = evento.target.closest("[data-item-id]");
        if (!linha) return;

        const id = linha.dataset.itemId;

        if (evento.target.closest(".pdv-salvar-item")) {
            try {
                const payload = await post(
                    urlItem(app.dataset.alterarUrlBase, id),
                    {
                        quantidade: linha.querySelector(".pdv-quantidade").value,
                        desconto: linha.querySelector(".pdv-desconto-item").value,
                    }
                );

                renderVenda(payload.venda);
                mostrarAlerta("Item atualizado.", "success");
            } catch (erro) {
                mostrarAlerta(erro.message);
            }
        }

        if (evento.target.closest(".pdv-remover-item")) {
            if (!window.confirm("Remover este item da venda?")) return;

            try {
                const payload = await post(
                    urlItem(app.dataset.cancelarUrlBase, id),
                    { motivo: "Removido na frente de caixa." }
                );

                renderVenda(payload.venda);
                mostrarAlerta("Item removido.", "success");
            } catch (erro) {
                mostrarAlerta(erro.message);
            }
        }
    });

    const numero = (valor) => {
        const n = Number.parseFloat(String(valor || "0").replace(",", "."));
        return Number.isFinite(n) ? n : 0;
    };

    const beneficioAtual = () => {
        const tipoSelecionado = document.querySelector('input[name="pdv-beneficio"]:checked')?.value || "nenhum";
        const b = vendaAtual?.beneficios || {};
        if (voucherAplicado) {
            return { tipo: "voucher", valor: numero(voucherAplicado.desconto), codigo: voucherAplicado.codigo };
        }
        if (tipoSelecionado === "cashback") {
            const informado = numero(document.getElementById("pdv-fechamento-cashback-valor").value);
            return { tipo: "cashback", valor: Math.min(informado, numero(b.cashback_disponivel), numero(vendaAtual.total)), codigo: "" };
        }
        return { tipo: "nenhum", valor: 0, codigo: "" };
    };

    const totalLiquido = () => Math.max(0, numero(vendaAtual?.total) - beneficioAtual().valor);

    const resumoPagamentos = () => {
        const total = totalLiquido();
        const pago = [...document.querySelectorAll(".pdv-valor-pagamento")]
            .reduce((s, el) => s + numero(el.value), 0);
        const diferenca = Number((total - pago).toFixed(2));
        return {
            total,
            pago,
            restante: Math.max(0, diferenca),
            excedente: Math.max(0, -diferenca),
            quitado: Math.abs(diferenca) < 0.01,
        };
    };

    const atualizarResumoFechamento = () => {
        if (!vendaAtual) return;
        const beneficio = beneficioAtual();
        const resumo = resumoPagamentos();
        const restante = document.getElementById("pdv-fechamento-restante");
        const botao = document.getElementById("pdv-confirmar-fechamento");

        document.getElementById("pdv-fechamento-total-original").textContent = moeda(vendaAtual.total);
        document.getElementById("pdv-fechamento-beneficio").textContent = moeda(beneficio.valor);
        const descontoGeral = document.getElementById("pdv-desconto-geral");
        if (descontoGeral) descontoGeral.value = beneficio.valor.toFixed(2);
        document.getElementById("pdv-fechamento-total-pagar").textContent = moeda(resumo.total);

        restante.textContent = resumo.excedente > 0
            ? `Excedente ${moeda(resumo.excedente)}`
            : moeda(resumo.restante);
        restante.classList.toggle("text-danger", !resumo.quitado);
        restante.classList.toggle("text-success", resumo.quitado);

        if (botao) botao.disabled = !resumo.quitado;
        return resumo;
    };

    const formaLinha = (linha) => formasPagamento.find(
        (f) => String(f.id) === linha.querySelector(".pdv-forma-pagamento").value
    );

    const atualizarLinha = (linha, origem = null) => {
        const forma = formaLinha(linha);
        if (!forma) return;

        const valor = linha.querySelector(".pdv-valor-pagamento");
        const parcelas = linha.querySelector(".pdv-parcelas");
        const recebido = linha.querySelector(".pdv-valor-recebido");

        parcelas.disabled = !forma.permite_parcelamento;
        parcelas.max = forma.maximo_parcelas || 1;
        if (!forma.permite_parcelamento) parcelas.value = 1;

        recebido.disabled = false;
        recebido.placeholder = forma.permite_troco
            ? "Valor entregue"
            : "Valor recebido";

        if (forma.permite_troco) {
            if (!recebido.value && numero(valor.value) > 0) {
                recebido.value = numero(valor.value).toFixed(2);
            }
        } else if (origem === recebido) {
            valor.value = numero(recebido.value) > 0
                ? numero(recebido.value).toFixed(2)
                : "";
        } else {
            recebido.value = numero(valor.value) > 0
                ? numero(valor.value).toFixed(2)
                : "";
        }

        const troco = forma.permite_troco
            ? Math.max(0, numero(recebido.value) - numero(valor.value))
            : 0;
        linha.querySelector(".pdv-troco").textContent = moeda(troco);
    };

    const adicionarPagamento = (valor = "") => {
        const linha = document.createElement("tr");
        linha.className = "pdv-linha-pagamento";
        linha.innerHTML = `
          <td><select class="form-select pdv-forma-pagamento">${formasPagamento.map(
              (f) => `<option value="${f.id}">${escapar(f.nome)}</option>`
          ).join("")}</select></td>
          <td><input class="form-control text-end pdv-valor-pagamento" type="number" min="0.01" step="0.01" value="${valor}"></td>
          <td><input class="form-control text-end pdv-parcelas" type="number" min="1" step="1" value="1"></td>
          <td><input class="form-control text-end pdv-valor-recebido" type="number" min="0" step="0.01" disabled></td>
          <td class="text-end pdv-troco">R$ 0,00</td>
          <td><button class="btn btn-outline-danger btn-sm pdv-remover-pagamento" type="button">×</button></td>`;
        document.getElementById("pdv-pagamentos").appendChild(linha);
        atualizarLinha(linha);
        atualizarResumoFechamento();
    };

    const erroFechamento = (mensagem = "") => {
        const alertaModal = document.getElementById("pdv-fechamento-alerta");
        alertaModal.textContent = mensagem;
        alertaModal.classList.toggle("d-none", !mensagem);
    };

    const abrirFechamento = async () => {
        if (!botaoFinalizar || botaoFinalizar.disabled) return;
        erroFechamento("");
        try {
            const resposta = await fetch(app.dataset.opcoesFechamentoUrl, {
                headers: { "X-Requested-With": "XMLHttpRequest" },
            });
            const payload = await resposta.json();
            if (!resposta.ok || !payload.ok) throw new Error(payload.erro || "Falha ao abrir fechamento.");

            vendaAtual = payload.venda;
            formasPagamento = payload.formas_pagamento || [];
            if (!formasPagamento.length) throw new Error("Nenhuma forma de pagamento ativa.");

            const b = vendaAtual.beneficios || {};
            const voucherResumo = document.getElementById("pdv-fechamento-voucher");
            voucherResumo.textContent = voucherAplicado
                ? `${voucherAplicado.codigo} - ${voucherAplicado.nome} (${moeda(voucherAplicado.desconto)})`
                : "Nenhum voucher aplicado.";
            document.getElementById("pdv-fechamento-cashback-disponivel").textContent = moeda(b.cashback_disponivel);
            const opcaoVoucher = document.querySelector('input[name="pdv-beneficio"][value="voucher"]');
            if (opcaoVoucher) { opcaoVoucher.disabled = !voucherAplicado; opcaoVoucher.checked = Boolean(voucherAplicado); }
            const opcaoCashback = document.querySelector('input[name="pdv-beneficio"][value="cashback"]');
            if (opcaoCashback) opcaoCashback.disabled = Boolean(voucherAplicado) || numero(b.cashback_disponivel) <= 0;
            const opcaoNenhum = document.querySelector('input[name="pdv-beneficio"][value="nenhum"]');
            if (opcaoNenhum && !voucherAplicado) opcaoNenhum.checked = true;
            document.getElementById("pdv-fechamento-cashback-valor").value = "";
            document.getElementById("pdv-pagamentos").innerHTML = "";
            adicionarPagamento(totalLiquido().toFixed(2));

            modalFechamento = modalFechamento || new bootstrap.Modal(
                document.getElementById("pdv-modal-fechamento")
            );
            modalFechamento.show();
        } catch (erro) {
            mostrarAlerta(erro.message);
        }
    };

    const confirmarFechamento = async () => {
        const botao = document.getElementById("pdv-confirmar-fechamento");
        erroFechamento("");
        botao.disabled = true;
        const beneficio = beneficioAtual();
        const resumo = resumoPagamentos();

        if (!resumo.quitado) {
            erroFechamento(
                resumo.excedente > 0
                    ? `Os pagamentos excedem o total em ${moeda(resumo.excedente)}.`
                    : `Ainda falta receber ${moeda(resumo.restante)}.`
            );
            botao.disabled = false;
            return;
        }

        const linhasPagamento = [...document.querySelectorAll(".pdv-linha-pagamento")];
        if (!linhasPagamento.length) {
            erroFechamento("Informe ao menos uma forma de pagamento.");
            botao.disabled = false;
            return;
        }

        for (const linha of linhasPagamento) {
            const forma = formaLinha(linha);
            const valor = numero(linha.querySelector(".pdv-valor-pagamento").value);
            const recebido = numero(linha.querySelector(".pdv-valor-recebido").value);

            if (!forma || valor <= 0) {
                erroFechamento("Todos os pagamentos devem possuir forma e valor positivo.");
                botao.disabled = false;
                return;
            }

            if (forma.permite_troco && recebido < valor) {
                erroFechamento("No dinheiro, o valor recebido nao pode ser menor que o valor do pagamento.");
                botao.disabled = false;
                return;
            }

            if (!forma.permite_troco && Math.abs(recebido - valor) >= 0.01) {
                erroFechamento(`${forma.nome}: o valor recebido deve ser igual ao valor do pagamento.`);
                botao.disabled = false;
                return;
            }
        }

        const pagamentos = linhasPagamento.map((linha) => ({
            forma_pagamento_id: linha.querySelector(".pdv-forma-pagamento").value,
            valor: linha.querySelector(".pdv-valor-pagamento").value,
            parcelas: linha.querySelector(".pdv-parcelas").value,
            valor_recebido: linha.querySelector(".pdv-valor-recebido").value,
        }));
        try {
            const payload = await postJson(app.dataset.finalizarUrl, {
                tipo_beneficio: beneficio.tipo,
                desconto_geral: beneficio.valor.toFixed(2),
                valor_cashback: beneficio.tipo === "cashback" ? beneficio.valor.toFixed(2) : "0.00",
                codigo_voucher: beneficio.codigo,
                pagamentos,
            });
            modalFechamento.hide();
            voucherAplicado = null;
            renderVoucherAplicado();
            limparModalFechamento();
            mostrarAlerta(payload.mensagem || "Venda finalizada com sucesso.", "success");
            await carregarEstado();
        } catch (erro) {
            erroFechamento(erro.message);
        } finally {
            botao.disabled = false;
        }
    };


    const renderVoucherAplicado = () => {
        const form = document.getElementById("pdv-voucher-form");
        const painel = document.getElementById("pdv-voucher-aplicado");
        const nome = document.getElementById("pdv-voucher-aplicado-nome");
        const detalhes = document.getElementById("pdv-voucher-aplicado-detalhes");
        form?.classList.toggle("d-none", Boolean(voucherAplicado));
        painel?.classList.toggle("d-none", !voucherAplicado);
        if (voucherAplicado) {
            nome.textContent = `${voucherAplicado.codigo} - ${voucherAplicado.nome}`;
            detalhes.textContent = `Desconto: ${moeda(voucherAplicado.desconto)}` + (voucherAplicado.cliente ? ` | Cliente: ${voucherAplicado.cliente}` : "");
        } else { nome.textContent = ""; detalhes.textContent = ""; }
    };

    const aplicarVoucher = async () => {
        if (!vendaAtual?.id) { mostrarAlerta("Adicione um produto antes de aplicar o voucher.", "warning"); return; }
        const campo = document.getElementById("pdv-voucher-codigo");
        const codigo = campo.value.trim().toUpperCase();
        if (!codigo) { mostrarAlerta("Informe o codigo do voucher.", "warning"); campo.focus(); return; }
        const botao = document.getElementById("pdv-aplicar-voucher");
        botao.disabled = true;
        limparAlerta();
        try {
            const payload = await post(app.dataset.validarVoucherUrl, { codigo });
            voucherAplicado = payload.voucher;
            campo.value = "";
            renderVoucherAplicado();
            mostrarAlerta("Voucher aplicado a esta venda.", "success");
        } catch (erro) { mostrarAlerta(erro.message); }
        finally { botao.disabled = false; }
    };

    const removerVoucher = () => {
        voucherAplicado = null;
        document.getElementById("pdv-voucher-codigo").value = "";
        renderVoucherAplicado();
        mostrarAlerta("Voucher removido da venda.", "success");
    };

    const limparModalFechamento = () => {
        erroFechamento("");
        document.getElementById("pdv-pagamentos").innerHTML = "";
        document.getElementById("pdv-fechamento-cashback-valor").value = "";
    };

    const cancelarVenda = async () => {
        if (!window.confirm("Cancelar toda a venda? Itens, cliente, vendedor, voucher e pagamentos serao removidos.")) return;

        const botao = document.getElementById("pdv-cancelar-venda");
        if (!botao) {
            mostrarAlerta("Botao de cancelamento nao encontrado.", "danger");
            return;
        }

        botao.disabled = true;
        erroFechamento("");

        try {
            const payload = await post(app.dataset.cancelarVendaUrl, {});
            voucherAplicado = null;
            renderVoucherAplicado();
            limparModalFechamento();
            modalFechamento?.hide();
            resultados.innerHTML = "";
            resultadosClientes.innerHTML = "";
            busca.value = "";
            buscaCliente.value = "";
            await carregarEstado();
            mostrarAlerta(payload.mensagem || "Venda cancelada. Nova venda iniciada.", "success");
            busca.focus();
        } catch (erro) {
            mostrarAlerta(erro.message || "Nao foi possivel cancelar a venda.", "danger");
            erroFechamento(erro.message || "Nao foi possivel cancelar a venda.");
        } finally {
            botao.disabled = false;
        }
    };

    document.getElementById("pdv-aplicar-voucher")?.addEventListener("click", aplicarVoucher);
    document.getElementById("pdv-voucher-codigo")?.addEventListener("keydown", (evento) => {
        if (evento.key === "Enter") { evento.preventDefault(); aplicarVoucher(); }
    });
    document.getElementById("pdv-remover-voucher")?.addEventListener("click", removerVoucher);


    document.getElementById("pdv-cancelar-venda")?.addEventListener("click", cancelarVenda);

    botaoFinalizar?.addEventListener("click", abrirFechamento);
    document.getElementById("pdv-confirmar-fechamento")?.addEventListener("click", confirmarFechamento);
    document.getElementById("pdv-adicionar-pagamento")?.addEventListener("click", () => {
        const restante = resumoPagamentos().restante;
        adicionarPagamento(restante > 0 ? restante.toFixed(2) : "");
    });
    document.getElementById("pdv-pagamentos")?.addEventListener("input", (e) => {
        const linha = e.target.closest(".pdv-linha-pagamento");
        if (linha) atualizarLinha(linha, e.target);
        atualizarResumoFechamento();
    });
    document.getElementById("pdv-pagamentos")?.addEventListener("change", (e) => {
        const linha = e.target.closest(".pdv-linha-pagamento");
        if (linha) atualizarLinha(linha, e.target);
        atualizarResumoFechamento();
    });
    document.getElementById("pdv-pagamentos")?.addEventListener("click", (e) => {
        const remover = e.target.closest(".pdv-remover-pagamento");
        if (remover) {
            remover.closest(".pdv-linha-pagamento").remove();
            atualizarResumoFechamento();
        }
    });
    document.querySelectorAll('input[name="pdv-beneficio"]').forEach((el) =>
        el.addEventListener("change", () => {
            const linhas = document.querySelectorAll(".pdv-linha-pagamento");
            if (linhas.length === 1) linhas[0].querySelector(".pdv-valor-pagamento").value = totalLiquido().toFixed(2);
            atualizarResumoFechamento();
        })
    );
    document.getElementById("pdv-fechamento-cashback-valor")?.addEventListener("input", () => {
        const linhas = document.querySelectorAll(".pdv-linha-pagamento");
        if (linhas.length === 1) linhas[0].querySelector(".pdv-valor-pagamento").value = totalLiquido().toFixed(2);
        atualizarResumoFechamento();
    });

    document.addEventListener("keydown", (evento) => {
        if (evento.key === "F2") {
            evento.preventDefault();
            busca?.focus();
        }

        if (evento.key === "F6") {
            evento.preventDefault();
            abrirFechamento();
        }

        if (evento.key === "Escape") {
            resultados.innerHTML = "";

            if (busca) {
                busca.value = "";
                busca.focus();
            }
        }
    });

    if (caixaAberto) {
        carregarVendedores().then(carregarEstado);
    }
})();
