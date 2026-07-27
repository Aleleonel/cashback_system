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
    const cashbackDisponivel = document.getElementById("pdv-cashback-disponivel");
    const voucherRecomendado = document.getElementById("pdv-voucher-recomendado");
    const descontoRecomendado = document.getElementById("pdv-desconto-recomendado");
    const cashbackPrevisto = document.getElementById("pdv-cashback-previsto");
    const vazio = document.getElementById("pdv-vazio");
    const alerta = document.getElementById("pdv-alerta");
    const caixaAberto = app.dataset.caixaAberto === "true";

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

    const urlItem = (base, id) => base.replace("/0/", `/${id}/`);

    const renderVenda = (venda) => {
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
        document.getElementById("pdv-status-venda").textContent =
            venda.id ? `Venda em rascunho #${venda.id}` : "Nova venda";

        if (venda.cliente) {
            clienteNome.textContent = venda.cliente.nome;
            clienteDocumento.textContent =
                venda.cliente.cpf || venda.cliente.telefone || "Cliente identificado";
        }
        if (venda.vendedor) {
            vendedorAtual.textContent = venda.vendedor.nome;
            if (vendedorSelect.querySelector(`option[value="${venda.vendedor.id}"]`)) {
                vendedorSelect.value = String(venda.vendedor.id);
            }
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

    document.addEventListener("keydown", (evento) => {
        if (evento.key === "F2") {
            evento.preventDefault();
            busca?.focus();
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
