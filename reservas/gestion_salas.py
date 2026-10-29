from datetime import datetime, time
import re

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from cuentas.services import ROL_ADMINISTRADOR, usuario_tiene_rol
from .models import Horario, Reserva, Sala, SalaHorario, Usuario


class GestionSalasError(Exception):
    """Regla de gestión incumplida; el formulario puede mostrar este mensaje."""


@transaction.atomic
def create_room(codigo_usuario_admin, nombre_sala):
    """Crea una sala activa sin repetir nombres (incluso con distinto uso de mayúsculas)."""
    _validar_gestion_habilitada()
    _validar_administrador(codigo_usuario_admin)
    nombre = _validar_nombre_sala(nombre_sala)
    _validar_sala_no_duplicada(nombre)
    return Sala.objects.create(nombre_sala=nombre)


@transaction.atomic
def create_room_schedule(codigo_usuario_admin, id_sala, hora_inicio, hora_fin):
    """Añade un bloque a una sala sin alterar sus asignaciones anteriores."""
    _validar_gestion_habilitada()
    _validar_administrador(codigo_usuario_admin)
    inicio, fin = _validar_intervalo(hora_inicio, hora_fin)
    sala = _obtener_sala_activa_y_bloquear(id_sala)
    horarios_actuales = _obtener_horarios_de_sala(sala)
    _validar_sin_duplicados(inicio, fin, horarios_actuales)
    _validar_sin_superposicion(inicio, fin, horarios_actuales)
    _validar_separacion_limpieza(inicio, fin, horarios_actuales)
    horario, _ = Horario.objects.get_or_create(hora_inicio=inicio, hora_fin=fin)
    asignacion_retirada = SalaHorario.objects.filter(
        sala=sala, horario=horario,
        estado_sala_horario=SalaHorario.ESTADO_RETIRADO,
    ).first()
    if asignacion_retirada is not None:
        asignacion_retirada.estado_sala_horario = SalaHorario.ESTADO_DISPONIBLE
        asignacion_retirada.save(update_fields=["estado_sala_horario"])
        return asignacion_retirada
    return SalaHorario.objects.create(sala=sala, horario=horario)


@transaction.atomic
def remove_room_schedule(codigo_usuario_admin, id_sala_horario):
    """Retira un horario de una sala sin borrar reservas ni historial."""
    _validar_gestion_habilitada()
    _validar_administrador(codigo_usuario_admin)
    try:
        id_sala_horario = int(id_sala_horario)
    except (ValueError, TypeError) as exc:
        raise GestionSalasError("Selecciona un horario válido.") from exc
    if not 0 < id_sala_horario <= 9223372036854775807:
        raise GestionSalasError("Selecciona un horario válido.")

    # Serializa la retirada con la creación de reservas en SQLite.
    if not SalaHorario.objects.filter(pk=id_sala_horario).update(
        estado_sala_horario=F("estado_sala_horario")
    ):
        raise GestionSalasError("El horario seleccionado no existe.")
    asignacion = SalaHorario.objects.select_related("sala", "horario").get(
        pk=id_sala_horario
    )
    if asignacion.estado_sala_horario == SalaHorario.ESTADO_RETIRADO:
        raise GestionSalasError("Ese horario ya fue retirado de la sala.")
    if asignacion.estado_sala_horario == SalaHorario.ESTADO_MANTENIMIENTO:
        raise GestionSalasError("Saca primero el horario de mantenimiento.")
    if Reserva.objects.filter(
        sala_horario=asignacion,
        fecha__gte=timezone.localdate(),
        estado_reserva__in=[Reserva.ESTADO_CONFIRMADA, "EN_USO"],
    ).exists():
        raise GestionSalasError(
            "Este horario tiene reservas activas. Modifícalas o cancélalas antes de retirarlo."
        )
    asignacion.estado_sala_horario = SalaHorario.ESTADO_RETIRADO
    asignacion.save(update_fields=["estado_sala_horario"])
    return asignacion


def _validar_gestion_habilitada():
    if not settings.GESTION_SALAS_HABILITADA:
        raise GestionSalasError("La gestión de salas y horarios está deshabilitada.")


def _validar_administrador(codigo):
    if not (Usuario.objects.filter(pk=codigo, estado_usuario=True).exists()
            and usuario_tiene_rol(codigo, ROL_ADMINISTRADOR)):
        raise GestionSalasError("Solo un administrador puede gestionar salas y horarios.")


def _validar_nombre_sala(nombre):
    nombre = " ".join(str(nombre or "").split())
    if not nombre:
        raise GestionSalasError("Escribe el nombre de la sala.")
    if len(nombre) > 100:
        raise GestionSalasError("El nombre no puede superar los 100 caracteres.")
    return nombre


def _validar_sala_no_duplicada(nombre):
    if any(" ".join(existente.split()).casefold() == nombre.casefold()
           for existente in Sala.objects.values_list("nombre_sala", flat=True)):
        raise GestionSalasError("Ya existe una sala con ese nombre.")


def _validar_intervalo(inicio, fin):
    inicio = _parsear_hora(inicio)
    fin = _parsear_hora(fin)
    minutos = (_minutos(fin) - _minutos(inicio))
    if minutos <= 0:
        raise GestionSalasError("La hora de fin debe ser posterior a la de inicio.")
    if minutos < 120:
        raise GestionSalasError("Un horario debe durar al menos 120 minutos (2 horas).")
    return inicio, fin


def _parsear_hora(valor):
    if isinstance(valor, time):
        if valor.second or valor.microsecond:
            raise GestionSalasError("Escribe horas completas en formato HH:MM.")
        return valor
    if not isinstance(valor, str) or not re.fullmatch(r"\d{2}:\d{2}", valor):
        raise GestionSalasError("Escribe una hora válida en formato HH:MM.")
    try:
        return datetime.strptime(valor, "%H:%M").time()
    except ValueError as exc:
        raise GestionSalasError("Escribe una hora válida en formato HH:MM.") from exc


def _minutos(valor):
    return valor.hour * 60 + valor.minute


def _obtener_sala_activa_y_bloquear(id_sala):
    try:
        id_sala = int(id_sala)
    except (ValueError, TypeError) as exc:
        raise GestionSalasError("Selecciona una sala válida.") from exc
    if not 0 < id_sala <= 9223372036854775807:
        raise GestionSalasError("Selecciona una sala válida.")
    # La escritura toma el bloqueo de SQLite ANTES de comprobar los intervalos,
    # evitando dos altas simultáneas que validen el mismo estado previo.
    if not Sala.objects.filter(pk=id_sala, estado_sala=True).update(
        estado_sala=F("estado_sala")
    ):
        raise GestionSalasError("La sala seleccionada no existe o está inactiva.")
    return Sala.objects.get(pk=id_sala)


def _obtener_horarios_de_sala(sala):
    """Lee solamente los horarios de esta sala, incluidos los bloqueados."""
    return [
        (_minutos(asignacion.horario.hora_inicio), _minutos(asignacion.horario.hora_fin))
        for asignacion in SalaHorario.objects.filter(sala=sala).exclude(
            estado_sala_horario=SalaHorario.ESTADO_RETIRADO
        ).select_related("horario")
    ]


def _validar_sin_duplicados(inicio, fin, horarios_actuales):
    nuevo = (_minutos(inicio), _minutos(fin))
    if nuevo in horarios_actuales:
        raise GestionSalasError("Ese horario ya está asignado a la sala.")


def _validar_sin_superposicion(inicio, fin, horarios_actuales):
    nuevo_inicio, nuevo_fin = _minutos(inicio), _minutos(fin)
    for actual_inicio, actual_fin in horarios_actuales:
        if nuevo_inicio < actual_fin and actual_inicio < nuevo_fin:
            raise GestionSalasError("El horario se superpone con otro de esa sala.")


def _validar_separacion_limpieza(inicio, fin, horarios_actuales):
    nuevo_inicio, nuevo_fin = _minutos(inicio), _minutos(fin)
    for actual_inicio, actual_fin in horarios_actuales:
        if nuevo_inicio < actual_fin + 15 and actual_inicio < nuevo_fin + 15:
            raise GestionSalasError("Debe haber al menos 15 minutos de separación entre horarios.")
