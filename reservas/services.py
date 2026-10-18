"""
Lógica de negocio del caso de uso RES-CU-02 (docs/sesion-07-modelos.md):
"Bloquear un horario de una sala por mantenimiento".

Flujo de `block_room_schedule_for_maintenance`, paso a paso:

    1. El Administrador selecciona la sala y el horario (= una fila de
       `sala_horario`) que quiere bloquear.
    2. El sistema valida que quien lo pide tenga rol Administrador   -> E1
       y que esa combinación sala+horario exista.                    -> E2
    3. El sistema verifica que no esté ya en MANTENIMIENTO.
    4. Busca las reservas CONFIRMADA asociadas a ese sala_horario.
    5. Las cambia a POR_MANTENIMIENTO (sin penalización).
    6. Cambia sala_horario.estado_sala_horario a MANTENIMIENTO.
    7. Registra el bloqueo (quién, motivo, fecha) en `bloqueos`.
    8. Devuelve el resultado, indicando qué reservas se cancelaron.

Todo ocurre dentro de UNA transacción: o se hacen todos los cambios, o no
se hace ninguno (por ejemplo, si algo falla en el paso 7, la sala no queda
en MANTENIMIENTO con reservas a medio cancelar).
"""

from datetime import datetime, timedelta
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from cuentas.services import ROL_ADMINISTRADOR, usuario_tiene_rol

from .models import Bloqueo, Reserva, SalaHorario, Horario, Sancion, Usuario

ACTIVIDADES = ("Tutoría", "Examen", "Tarea", "Proyecto")
ESTADOS_ACTIVOS = ("CONFIRMADA", "EN_USO")


class ReservationError(Exception):
    """Rechazo de una solicitud de reserva sin modificar datos."""


@transaction.atomic
def create_student_reservation(codigo_usuario, id_sala_horario, actividad):
    # SQLite serializa las escrituras. Tomar el bloqueo antes de consultar evita
    # que dos solicitudes validen simultáneamente los mismos datos antiguos.
    if not SalaHorario.objects.filter(pk=id_sala_horario).update(
        estado_sala_horario=F("estado_sala_horario")
    ):
        raise ReservationError("La sala y el horario seleccionados no existen.")
    usuario = Usuario.objects.filter(pk=codigo_usuario, estado_usuario=True).first()
    if usuario is None or not usuario.password_hash or not usuario.usuariorol_set.filter(
        rol__nombre_rol__in=["Solicitante", "Estudiante", "Administrador", "Operador"]
    ).exists():
        raise ReservationError("La cuenta no está habilitada para reservar.")
    ahora = timezone.localtime()
    hoy = ahora.date()
    if hoy.weekday() >= 5 or hoy.isoformat() in settings.RESERVAS_FERIADOS:
        raise ReservationError("Hoy no se realizan reservas: es fin de semana o feriado.")
    sancion = Sancion.objects.filter(
        usuario=usuario, fecha_inicio__lte=ahora, fecha_fin__gt=ahora
    ).order_by("-fecha_fin").first()
    if sancion:
        minutos = int((sancion.fecha_fin - ahora).total_seconds() / 60) + 1
        raise ReservationError(f"Sanción activa: {sancion.motivo}. Restan {minutos} minutos.")
    if actividad not in ACTIVIDADES:
        raise ReservationError("Selecciona una actividad de la lista.")
    sh = SalaHorario.objects.select_related("sala", "horario").get(pk=id_sala_horario)
    if not sh.sala.estado_sala or sh.estado_sala_horario != SalaHorario.ESTADO_DISPONIBLE:
        raise ReservationError("Este horario no está disponible o está en mantenimiento.")
    if sh.horario.hora_fin <= ahora.time():
        raise ReservationError("El bloque ya terminó. Elige otro horario.")
    activas = Reserva.objects.filter(fecha=hoy, estado_reserva__in=ESTADOS_ACTIVOS)
    if activas.filter(sala_horario=sh).exists():
        raise ReservationError("El bloque ya fue reservado por otro usuario. Elige otro horario disponible.")
    bloques = list(Horario.objects.order_by("hora_inicio", "hora_fin", "pk").values_list("pk", flat=True))
    indice = bloques.index(sh.horario_id)
    vecinos = bloques[max(0, indice - 1):indice + 2]
    if activas.filter(usuario=usuario, sala_horario__horario_id__in=vecinos).exists():
        raise ReservationError("Ya tienes una reserva en el mismo bloque o en uno consecutivo.")
    inicio = datetime.combine(hoy, sh.horario.hora_inicio)
    fin = datetime.combine(hoy, sh.horario.hora_fin)
    for reserva in activas.filter(sala_horario__sala=sh.sala).select_related("sala_horario__horario"):
        horario = reserva.sala_horario.horario
        otro_inicio = datetime.combine(hoy, horario.hora_inicio)
        otro_fin = datetime.combine(hoy, horario.hora_fin)
        if inicio < otro_fin + timedelta(minutes=15) and fin + timedelta(minutes=15) > otro_inicio:
            raise ReservationError("La sala necesita 15 minutos entre reservas para desalojo y limpieza.")
    return Reserva.objects.create(usuario=usuario, sala_horario=sh, fecha=hoy, tipo_actividad=actividad)


def get_student_panel():
    ahora = timezone.localtime()
    reservas = {
        r.sala_horario_id: r for r in Reserva.objects.filter(
            fecha=ahora.date(), estado_reserva__in=ESTADOS_ACTIVOS
        ).select_related("usuario")
    }
    columnas = {}
    for sh in SalaHorario.objects.filter(sala__estado_sala=True).select_related("sala", "horario").order_by(
        "sala__nombre_sala", "horario__hora_inicio"
    ):
        columna = columnas.setdefault(sh.sala_id, {"sala": sh.sala, "bloques": []})
        if sh.horario.hora_fin <= ahora.time():
            continue
        reserva = reservas.get(sh.pk)
        columna["bloques"].append({
            "horario": sh.horario, "id": sh.pk, "reserva": reserva,
            "expira": timezone.make_aware(datetime.combine(ahora.date(), sh.horario.hora_fin)).isoformat(),
            "disponible": not reserva and sh.estado_sala_horario == SalaHorario.ESTADO_DISPONIBLE,
            "mantenimiento": sh.estado_sala_horario == SalaHorario.ESTADO_MANTENIMIENTO,
            "color": reserva.usuario_id % 4 if reserva else 0,
        })
    return {
        "columnas": list(columnas.values()), "hoy": ahora.date(),
        "actividades": ACTIVIDADES,
        "dia_habilitado": ahora.weekday() < 5 and ahora.date().isoformat() not in settings.RESERVAS_FERIADOS,
    }


class ScheduleNotFoundError(Exception):
    """No existe esa combinación de sala y horario (rama E2)."""


class NotAuthorizedError(Exception):
    """Quien solicita el bloqueo no tiene rol de Administrador (rama E1)."""


class ScheduleAlreadyBlockedError(Exception):
    """Ese sala_horario ya está en estado MANTENIMIENTO."""


# --- Lecturas para mostrar el estado del sistema ----------------------------

def get_sala_horarios():
    return SalaHorario.objects.select_related("sala", "horario").order_by(
        "id_sala_horario"
    )


def get_reservas():
    return Reserva.objects.select_related(
        "usuario", "sala_horario__sala", "sala_horario__horario"
    ).order_by("id_reserva")


def get_bloqueos():
    return Bloqueo.objects.select_related(
        "usuario", "sala_horario__sala", "sala_horario__horario"
    ).order_by("-fecha")


# --- Caso de uso RES-CU-02 --------------------------------------------------

@transaction.atomic
def block_room_schedule_for_maintenance(codigo_usuario_admin, id_sala_horario, motivo):
    """
    Bloquea por mantenimiento una combinación sala+horario.

    Lanza NotAuthorizedError (E1), ScheduleNotFoundError (E2) o
    ScheduleAlreadyBlockedError si el sistema debe rechazar la operación.
    """
    # Paso 2 (parte 1) — E1: sin permisos de Administrador
    if not usuario_tiene_rol(codigo_usuario_admin, ROL_ADMINISTRADOR):
        raise NotAuthorizedError(
            "No tienes permisos para bloquear salas. Contacta al administrador."
        )

    # Paso 2 (parte 2) — E2: la combinación sala+horario no existe
    try:
        sala_horario = SalaHorario.objects.select_related("sala", "horario").get(
            pk=id_sala_horario
        )
    except SalaHorario.DoesNotExist:
        raise ScheduleNotFoundError(
            f"No existe una combinación de sala y horario con id {id_sala_horario}."
        )

    # Paso 3 — ya está en mantenimiento
    if sala_horario.estado_sala_horario == SalaHorario.ESTADO_MANTENIMIENTO:
        raise ScheduleAlreadyBlockedError(
            f"El horario {sala_horario.horario} de la sala "
            f"{sala_horario.sala} ya está en mantenimiento."
        )

    # Paso 4 y 5 — reservas CONFIRMADA -> POR_MANTENIMIENTO (sin penalización)
    reservas_canceladas = list(
        Reserva.objects.select_related("usuario").filter(
            sala_horario=sala_horario,
            estado_reserva=Reserva.ESTADO_CONFIRMADA,
        )
    )
    Reserva.objects.filter(pk__in=[r.pk for r in reservas_canceladas]).update(
        estado_reserva=Reserva.ESTADO_POR_MANTENIMIENTO
    )

    # Paso 6 — el horario de la sala pasa a MANTENIMIENTO
    sala_horario.estado_sala_horario = SalaHorario.ESTADO_MANTENIMIENTO
    sala_horario.save(update_fields=["estado_sala_horario"])

    # Paso 7 — registrar el bloqueo (quién, motivo, cuándo)
    Bloqueo.objects.create(
        usuario_id=codigo_usuario_admin,
        sala_horario=sala_horario,
        motivo=motivo,
    )

    # Paso 8 — confirmar el resultado
    return {
        "sala_horario": sala_horario,
        "reservas_canceladas": reservas_canceladas,
    }
