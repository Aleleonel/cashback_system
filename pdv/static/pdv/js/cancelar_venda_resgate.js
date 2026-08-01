(() => {
    "use strict";

    const app = document.getElementById("pdv-app");
    const button = document.getElementById("pdv-cancelar-venda");

    if (!app || !button) return;
    if (button.dataset.cancelarVendaResgateAtivo === "true") return;

    button.dataset.cancelarVendaResgateAtivo = "true";

    const getCookie = (name) => {
        const prefix = `${name}=`;
        const parts = document.cookie ? document.cookie.split(";") : [];

        for (const rawPart of parts) {
            const part = rawPart.trim();

            if (part.startsWith(prefix)) {
                return decodeURIComponent(part.slice(prefix.length));
            }
        }

        return "";
    };

    const validCsrfToken = (value) => {
        return typeof value === "string" &&
            (value.length === 32 || value.length === 64) &&
            /^[A-Za-z0-9]+$/.test(value);
    };

    const csrfToken = () => {
        const input = document.querySelector(
            'input[name="csrfmiddlewaretoken"]'
        );

        const inputToken = input?.value?.trim() || "";

        if (validCsrfToken(inputToken)) {
            return inputToken;
        }

        const cookieToken = getCookie("csrftoken").trim();

        if (validCsrfToken(cookieToken)) {
            return cookieToken;
        }

        return "";
    };

    const parseResponse = async (response) => {
        const contentType = response.headers.get("content-type") || "";

        if (contentType.includes("application/json")) {
            try {
                return await response.json();
            } catch {
                return {
                    ok: false,
                    erro: "O servidor retornou uma resposta JSON invalida.",
                };
            }
        }

        if (response.status === 403) {
            return {
                ok: false,
                erro: "A sessao de seguranca expirou. Recarregue a pagina e tente novamente.",
            };
        }

        return {
            ok: false,
            erro: `Nao foi possivel cancelar a venda. Codigo HTTP ${response.status}.`,
        };
    };

    const showError = (message) => {
        const safeMessage =
            typeof message === "string" && message.length <= 300
                ? message
                : "Nao foi possivel cancelar a venda.";

        const alertBox = document.getElementById("pdv-alerta");

        if (alertBox) {
            alertBox.textContent = safeMessage;
            alertBox.classList.remove("d-none");
            alertBox.classList.remove("alert-success", "alert-warning");
            alertBox.classList.add("alert-danger");
            alertBox.scrollIntoView({ block: "nearest" });
            return;
        }

        window.alert(safeMessage);
    };

    button.addEventListener(
        "click",
        async (event) => {
            event.preventDefault();
            event.stopPropagation();
            event.stopImmediatePropagation();

            const url = app.dataset.cancelarVendaUrl;

            if (!url) {
                showError("A URL de cancelamento nao esta disponivel.");
                return;
            }

            const token = csrfToken();

            if (!token) {
                showError(
                    "A sessao de seguranca nao esta disponivel. Recarregue a pagina e tente novamente."
                );
                return;
            }

            const confirmed = window.confirm(
                "Cancelar toda a venda? Itens, cliente, vendedor, voucher e pagamentos serao removidos."
            );

            if (!confirmed) return;

            button.disabled = true;

            try {
                const body = new URLSearchParams();
                body.set("csrfmiddlewaretoken", token);

                const response = await fetch(url, {
                    method: "POST",
                    credentials: "same-origin",
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                        "X-CSRFToken": token,
                        "X-Requested-With": "XMLHttpRequest",
                    },
                    body: body.toString(),
                });

                const payload = await parseResponse(response);

                if (!response.ok || !payload.ok) {
                    throw new Error(
                        payload.erro ||
                        payload.mensagem ||
                        "Nao foi possivel cancelar a venda."
                    );
                }

                window.location.reload();
            } catch (error) {
                button.disabled = false;
                showError(
                    error?.message ||
                    "Nao foi possivel cancelar a venda."
                );
            }
        },
        true
    );
})();