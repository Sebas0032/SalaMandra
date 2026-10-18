// Solo selecciona sala/horario; la validación y la reserva ocurren en Django.
const salas = document.querySelectorAll('input[name="sala"]');
const horarios = document.querySelectorAll('.horario');
horarios.forEach((opcion) => {
    opcion.dataset.bloqueado = String(opcion.querySelector('input').disabled);
});

function mostrarHorarios(sala) {
    let visibles = 0;
    let disponibles = 0;
    horarios.forEach((opcion) => {
        opcion.hidden = opcion.dataset.sala !== sala || Date.parse(opcion.dataset.expira) <= Date.now();
        const input = opcion.querySelector('input');
        input.disabled = opcion.hidden || opcion.dataset.bloqueado === 'true';
        if (input.disabled) input.checked = false;
        if (opcion.hidden) input.checked = false;
        else visibles++;
        if (!input.disabled) disponibles++;
    });
    document.getElementById('sin-horarios').hidden = visibles > 0;
    document.querySelector('.confirmar').disabled = disponibles === 0;
}

salas.forEach((sala) => sala.addEventListener('change', () => mostrarHorarios(sala.value)));
document.querySelectorAll('button[data-bloque]').forEach((boton) => {
    boton.addEventListener('click', () => {
        const sala = Array.from(salas).find((input) => input.value === boton.dataset.sala);
        sala.checked = true;
        mostrarHorarios(sala.value);
        const horario = document.querySelector(`input[name="id_sala_horario"][value="${boton.dataset.bloque}"]`);
        if (!horario.disabled) horario.checked = true;
        document.getElementById('actividad').focus();
    });
});
const seleccionada = document.querySelector('input[name="sala"]:checked');
if (seleccionada) mostrarHorarios(seleccionada.value);

// Oculta bloques finalizados aunque la página permanezca abierta.
function ocultarFinalizados() {
    document.querySelectorAll('[data-expira]').forEach((elemento) => {
        if (Date.parse(elemento.dataset.expira) <= Date.now()) {
            elemento.hidden = true;
            const input = elemento.querySelector('input');
            if (input) { input.checked = false; input.disabled = true; }
        }
    });
    const sala = document.querySelector('input[name="sala"]:checked');
    if (sala) mostrarHorarios(sala.value);
}
setInterval(ocultarFinalizados, 15000);
