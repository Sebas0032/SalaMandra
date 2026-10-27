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
ANTICIPACION_MINIMA_MODIFICACION = timedelta(hours=1)


class ReservationError(Exception):
    """Rechazo de una solicitud de reserva sin modificar datos."""


@transaction.atomic
def create_student_reservation(codigo_usuario, id_sala_horario, actividad):
    """Valida las reglas y crea una reserva para hoy en una transacción."""
    _bloquear_sala_horario(id_sala_horario)
    usuario = _obtener_usuario_reservante(codigo_usuario)
    ahora = timezone.localtime()
    hoy = ahora.date()
    sala_horario = _obtener_sala_horario(id_sala_horario)
    _validar_reglas_reserva(usuario, sala_horario, actividad, hoy, ahora)

    return Reserva.objects.create(
        usuario=usuario, sala_horario=sala_horario, fecha=hoy,
        tipo_actividad=actividad,
    )


@transaction.atomic
def modify_student_reservation(codigo_usuario, id_reserva, id_sala_horario):
    """Cambia la sala y el horario sin liberar antes la reserva original."""
    usuario = _obtener_usuario_reservante(codigo_usuario)
    reserva = _obtener_reserva_confirmada_del_usuario(
        usuario, id_reserva, bloquear=True
    )
    ahora = timezone.localtime()
    _validar_plazo_modificacion(reserva, ahora)

    _bloquear_sala_horario(id_sala_horario)
    nuevo_sala_horario = _obtener_sala_horario(id_sala_horario)
    _validar_reglas_reserva(
        usuario,
        nuevo_sala_horario,
        reserva.tipo_actividad,
        reserva.fecha,
        ahora,
        reserva_excluida_id=reserva.pk,
    )

    # El cambio se guarda únicamente después de superar todas las validaciones.
    reserva.sala_horario = nuevo_sala_horario
    reserva.save(update_fields=["sala_horario"])
    return reserva


def _validar_reglas_reserva(
    usuario,
    sala_horario,
    actividad,
    fecha,
    ahora,
    reserva_excluida_id=None,
):
    """Aplica las reglas compartidas por la creación y la modificación."""
    _validar_dia_habil(fecha)
    _validar_sin_sancion(usuario, ahora)
    _validar_actividad(actividad)
    _validar_bloque_disponible(sala_horario, ahora, fecha)

    reservas_activas = _obtener_reservas_activas(fecha)
    if reserva_excluida_id is not None:
        reservas_activas = reservas_activas.exclude(pk=reserva_excluida_id)
    _validar_bloque_no_reservado(sala_horario, reservas_activas)
    _validar_sin_bloques_consecutivos(usuario, sala_horario, reservas_activas)
    _validar_intervalo_limpieza(sala_horario, fecha, reservas_activas)


def _bloquear_sala_horario(id_sala_horario):
    # SQLite serializa las escrituras. Tomar el bloqueo antes de consultar evita
    # que dos solicitudes validen simultáneamente los mismos datos antiguos.
    if not SalaHorario.objects.filter(pk=id_sala_horario).update(
        estado_sala_horario=F("estado_sala_horario")
    ):
        raise ReservationError("La sala y el horario seleccionados no existen.")


def _obtener_usuario_reservante(codigo_usuario):
    usuario = Usuario.objects.filter(pk=codigo_usuario, estado_usuario=True).first()
    if usuario is None or not usuario.password_hash or not usuario.usuariorol_set.filter(
        rol__nombre_rol__in=["Solicitante", "Estudiante", "Administrador", "Operador"]
    ).exists():
        raise ReservationError("La cuenta no está habilitada para reservar.")
    return usuario


def _obtener_reserva_confirmada_del_usuario(usuario, id_reserva, bloquear=False):
    consulta = Reserva.objects.select_related(
        "sala_horario__sala", "sala_horario__horario"
    )
    if bloquear:
        consulta = consulta.select_for_update()
    try:
        return consulta.get(
            pk=id_reserva,
            usuario=usuario,
            estado_reserva=Reserva.ESTADO_CONFIRMADA,
        )
    except Reserva.DoesNotExist as exc:
        raise ReservationError(
            "La reserva no existe, no te pertenece o ya no está confirmada."
        ) from exc


def _inicio_de_reserva(reserva):
    return timezone.make_aware(
        datetime.combine(
            reserva.fecha, reserva.sala_horario.horario.hora_inicio
        )
    )


def _validar_plazo_modificacion(reserva, ahora):
    if ahora > _inicio_de_reserva(reserva) - ANTICIPACION_MINIMA_MODIFICACION:
        raise ReservationError(
            "La reserva solo se puede modificar con al menos 60 minutos "
            "de anticipación. La reserva original se conserva sin cambios."
        )


def _puede_modificar_reserva(reserva, ahora):
    return (
        reserva.estado_reserva == Reserva.ESTADO_CONFIRMADA
        and ahora
        <= _inicio_de_reserva(reserva) - ANTICIPACION_MINIMA_MODIFICACION
    )


def _validar_dia_habil(fecha):
    if not _es_dia_habilitado(fecha):
        raise ReservationError("Hoy no se realizan reservas: es fin de semana o feriado.")


def _es_dia_habilitado(fecha):
    return fecha.weekday() < 5 and fecha.isoformat() not in settings.RESERVAS_FERIADOS


def _validar_sin_sancion(usuario, ahora):
    sancion = Sancion.objects.filter(
        usuario=usuario, fecha_inicio__lte=ahora, fecha_fin__gt=ahora
    ).order_by("-fecha_fin").first()
    if sancion:
        minutos = int((sancion.fecha_fin - ahora).total_seconds() / 60) + 1
        raise ReservationError(f"Sanción activa: {sancion.motivo}. Restan {minutos} minutos.")


def _validar_actividad(actividad):
    if actividad not in ACTIVIDADES:
        raise ReservationError("Selecciona una actividad de la lista.")


def _obtener_sala_horario(id_sala_horario):
    return SalaHorario.objects.select_related("sala", "horario").get(pk=id_sala_horario)


def _validar_bloque_disponible(sala_horario, ahora, fecha):
    if (
        not sala_horario.sala.estado_sala
        or sala_horario.estado_sala_horario != SalaHorario.ESTADO_DISPONIBLE
    ):
        raise ReservationError("Este horario no está disponible o está en mantenimiento.")
    if fecha < ahora.date() or (
        fecha == ahora.date() and sala_horario.horario.hora_fin <= ahora.time()
    ):
        raise ReservationError("El bloque ya terminó. Elige otro horario.")


def _obtener_reservas_activas(fecha):
    return Reserva.objects.filter(fecha=fecha, estado_reserva__in=ESTADOS_ACTIVOS)


def _validar_bloque_no_reservado(sala_horario, reservas_activas):
    if reservas_activas.filter(sala_horario=sala_horario).exists():
        raise ReservationError("El bloque ya fue reservado por otro usuario. Elige otro horario disponible.")


def _validar_sin_bloques_consecutivos(usuario, sala_horario, reservas_activas):
    bloques = list(
        Horario.objects.order_by("hora_inicio", "hora_fin", "pk")
        .values_list("pk", flat=True)
    )
    indice = bloques.index(sala_horario.horario_id)
    vecinos = bloques[max(0, indice - 1):indice + 2]
    if reservas_activas.filter(usuario=usuario, sala_horario__horario_id__in=vecinos).exists():
        raise ReservationError("Ya tienes una reserva en el mismo bloque o en uno consecutivo.")


def _validar_intervalo_limpieza(sala_horario, fecha, reservas_activas):
    inicio = datetime.combine(fecha, sala_horario.horario.hora_inicio)
    fin = datetime.combine(fecha, sala_horario.horario.hora_fin)
    reservas_de_sala = reservas_activas.filter(
        sala_horario__sala=sala_horario.sala
    ).select_related("sala_horario__horario")
    for reserva in reservas_de_sala:
        horario = reserva.sala_horario.horario
        otro_inicio = datetime.combine(fecha, horario.hora_inicio)
        otro_fin = datetime.combine(fecha, horario.hora_fin)
        if inicio < otro_fin + timedelta(minutes=15) and fin + timedelta(minutes=15) > otro_inicio:
            raise ReservationError("La sala necesita 15 minutos entre reservas para desalojo y limpieza.")


def get_student_panel(codigo_usuario=None):
    """Prepara las salas, bloques y datos que necesita el panel del solicitante."""
    ahora = timezone.localtime()
    fecha = ahora.date()
    reservas_hoy = _obtener_reservas_de_hoy(fecha)
    columnas = _construir_columnas_salas(ahora, reservas_hoy)

    return {
        "columnas": columnas,
        "hoy": fecha,
        "actividades": ACTIVIDADES,
        "dia_habilitado": _es_dia_habilitado(fecha),
        "mis_reservas": _construir_mis_reservas(
            codigo_usuario, fecha, ahora
        ),
    }


def _construir_mis_reservas(codigo_usuario, fecha, ahora):
    if codigo_usuario is None:
        return []
    reservas = Reserva.objects.filter(
        usuario_id=codigo_usuario,
        fecha=fecha,
        estado_reserva__in=ESTADOS_ACTIVOS,
    ).select_related("sala_horario__sala", "sala_horario__horario").order_by(
        "sala_horario__horario__hora_inicio"
    )
    return [
        {
            "reserva": reserva,
            "puede_modificar": _puede_modificar_reserva(reserva, ahora),
        }
        for reserva in reservas
    ]


def _obtener_reservas_de_hoy(fecha):
    reservas = Reserva.objects.filter(
        fecha=fecha, estado_reserva__in=ESTADOS_ACTIVOS
    ).select_related("usuario")
    return {reserva.sala_horario_id: reserva for reserva in reservas}


def _construir_columnas_salas(ahora, reservas_hoy):
    columnas = {}
    sala_horarios = SalaHorario.objects.filter(sala__estado_sala=True).select_related(
        "sala", "horario"
    ).order_by(
        "sala__nombre_sala", "horario__hora_inicio"
    )

    for sala_horario in sala_horarios:
        columna = columnas.setdefault(
            sala_horario.sala_id,
            {"sala": sala_horario.sala, "bloques": []},
        )
        if sala_horario.horario.hora_fin <= ahora.time():
            continue
        reserva = reservas_hoy.get(sala_horario.pk)
        columna["bloques"].append(
            _construir_bloque_panel(sala_horario, reserva, ahora.date())
        )

    return list(columnas.values())


def _construir_bloque_panel(sala_horario, reserva, fecha):
    mantenimiento = (
        sala_horario.estado_sala_horario == SalaHorario.ESTADO_MANTENIMIENTO
    )
    disponible = (
        reserva is None
        and sala_horario.estado_sala_horario == SalaHorario.ESTADO_DISPONIBLE
    )
    expira = timezone.make_aware(
        datetime.combine(fecha, sala_horario.horario.hora_fin)
    ).isoformat()

    return {
        "horario": sala_horario.horario,
        "id": sala_horario.pk,
        "reserva": reserva,
        "expira": expira,
        "disponible": disponible,
        "mantenimiento": mantenimiento,
        "color": reserva.usuario_id % 4 if reserva else 0,
    }


def get_reservation_modification_panel(codigo_usuario, id_reserva):
    """Prepara la reserva y los destinos disponibles para modificarla."""
    usuario = _obtener_usuario_reservante(codigo_usuario)
    reserva = _obtener_reserva_confirmada_del_usuario(usuario, id_reserva)
    ahora = timezone.localtime()
    _validar_plazo_modificacion(reserva, ahora)

    reservas_fecha = _obtener_reservas_de_hoy(reserva.fecha)
    reservas_fecha.pop(reserva.sala_horario_id, None)
    return {
        "reserva": reserva,
        "columnas": _construir_columnas_salas(ahora, reservas_fecha),
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
