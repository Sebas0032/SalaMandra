// Filtra los horarios de la sala; el bloqueo sigue siendo de un horario por envío.
const sala = document.getElementById('sala');
const opciones = document.querySelectorAll('.seleccion-horario');
opciones.forEach((opcion) => {
    opcion.dataset.bloqueado = String(opcion.querySelector('input').disabled);
});
function filtrarHorarios() {
    let disponibles = 0;
    opciones.forEach((opcion) => {
        const input = opcion.querySelector('input');
        opcion.hidden = opcion.dataset.sala !== sala.value;
        input.disabled = opcion.hidden || opcion.dataset.bloqueado === 'true';
        if (input.disabled) input.checked = false;
        else disponibles++;
    });
    document.getElementById('sin-horarios').hidden = disponibles > 0;
    document.querySelector('.boton-bloqueo').disabled = disponibles === 0;
}
sala.addEventListener('change', filtrarHorarios);
filtrarHorarios();
