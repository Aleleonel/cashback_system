function mostrarStatus(tipo, texto) {

    const statusBox = document.getElementById('cliente-status');

    if (!statusBox) {
        return;
    }

    statusBox.className = 'alert mb-3 alert-' + tipo;
    statusBox.textContent = texto;
    statusBox.classList.remove('d-none');
}

function esconderStatus() {

    const statusBox = document.getElementById('cliente-status');

    if (!statusBox) {
        return;
    }

    statusBox.classList.add('d-none');
    statusBox.textContent = '';
}