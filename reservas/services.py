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

from cuentas.services import ROL_ADMINISTRADOR, ROL_OPERANTE
from .gestion_sanciones import contar_faltas, sanciones_vigentes

from .models import (
    Auditoria,
    Bloqueo,
    Desbloqueo,
    Horario,
    Notificacion,
    Reserva,
    Rol,
    SalaHorario,
    Sancion,
    TipoSancion,
    Usuario,
)

ACTIVIDADES = ("Tutoría", "Examen", "Tarea", "Proyecto")
ESTADOS_ACTIVOS = ("CONFIRMADA", "EN_USO")
ANTICIPACION_MINIMA_MODIFICACION = timedelta(hours=1)
ANTICIPACION_CANCELACION_SIN_SANCION = timedelta(hours=1)
RESTRINGIR_BLOQUEO_TRAS_INICIO = True
RESTRINGIR_DESBLOQUEO_TRAS_INICIO = True
ESCALA_SANCIONES_CANCELACION = (
    ("Cancelación tardía (1ra vez)", 24),
    ("Cancelación tardía (2da vez)", 48),
    ("Cancelación tardía (3ra vez)", 168),
    ("Cancelación tardía (4ta vez, todo el semestre)", 9999),
)


class ReservationError(Exception):
    """Rechazo de una solicitud de reserva sin modificar datos."""


@transaction.atomic
def create_student_reservation(codigo_usuario, id_sala_horario, actividad):
    """Crea una reserva propia y conserva la API del panel solicitante."""
    return create_reservation(
        codigo_actor=codigo_usuario,
        codigo_solicitante=codigo_usuario,
        id_sala_horario=id_sala_horario,
        actividad=actividad,
    )


@transaction.atomic
def create_reservation(
    codigo_actor, codigo_solicitante, id_sala_horario, actividad
):
    """Crea una reserva para un solicitante y audita al usuario que la ejecuta."""
    _bloquear_sala_horario(id_sala_horario)
    actor = _obtener_usuario_reservante(codigo_actor)
    solicitante = _obtener_solicitante(codigo_solicitante)
    _validar_actor_sobre_solicitante(actor, solicitante)
    ahora = timezone.localtime()
    hoy = ahora.date()
    sala_horario = _obtener_sala_horario(id_sala_horario)
    _validar_reglas_reserva(solicitante, sala_horario, actividad, hoy, ahora)

    reserva = Reserva.objects.create(
        usuario=solicitante, sala_horario=sala_horario, fecha=hoy,
        tipo_actividad=actividad,
    )
    Auditoria.objects.create(
        reserva=reserva, actor=actor, accion=Auditoria.Accion.CREAR,
        fecha_accion=ahora,
    )
    return reserva


@transaction.atomic
def modify_student_reservation(codigo_usuario, id_reserva, id_sala_horario):
    """Modifica una reserva propia y conserva la API del panel solicitante."""
    return modify_reservation(codigo_usuario, id_reserva, id_sala_horario)


@transaction.atomic
def modify_reservation(codigo_actor, id_reserva, id_sala_horario):
    """Modifica una reserva autorizada y audita al actor, no al titular."""
    actor = _obtener_usuario_reservante(codigo_actor)
    reserva = _obtener_reserva_confirmada(id_reserva, bloquear=True)
    _validar_acceso_reserva(actor, reserva)
    solicitante = reserva.usuario
    ahora = timezone.localtime()
    _validar_plazo_modificacion(reserva, ahora)

    _bloquear_sala_horario(id_sala_horario)
    nuevo_sala_horario = _obtener_sala_horario(id_sala_horario)
    _validar_reglas_reserva(
        solicitante,
        nuevo_sala_horario,
        reserva.tipo_actividad,
        reserva.fecha,
        ahora,
        reserva_excluida_id=reserva.pk,
    )

    # El cambio se guarda únicamente después de superar todas las validaciones.
    reserva.sala_horario = nuevo_sala_horario
    reserva.save(update_fields=["sala_horario"])
    Auditoria.objects.create(
        reserva=reserva, actor=actor, accion=Auditoria.Accion.MODIFICAR,
        fecha_accion=ahora,
    )
    return reserva


@transaction.atomic
def cancel_reservation(codigo_usuario_actor, id_reserva):
    """Cancela una reserva y audita al actor; el administrador nunca sanciona."""
    actor = _obtener_usuario_reservante(codigo_usuario_actor)
    reserva = _obtener_reserva_para_cancelar(actor, id_reserva)
    ahora = timezone.localtime()
    inicio = _inicio_de_reserva(reserva)
    if ahora >= inicio:
        raise ReservationError("La reserva ya comenzó y no se puede cancelar.")

    reserva.estado_reserva = Reserva.ESTADO_CANCELADA
    reserva.save(update_fields=["estado_reserva"])

    sancion = None
    if (
        actor.rol.nombre_rol != Rol.Nombre.ADMINISTRADOR
        and _cancelacion_es_tardia(reserva, ahora)
    ):
        sancion = _registrar_sancion_por_cancelacion(reserva.usuario_id, ahora)
    Auditoria.objects.create(
        reserva=reserva, actor=actor, accion=Auditoria.Accion.CANCELAR,
        fecha_accion=ahora,
    )
    _notificar_cancelacion_de_gestion(actor, reserva, ahora)
    return {"reserva": reserva, "sancion": sancion}


def _notificar_cancelacion_de_gestion(actor, reserva, ahora):
    """Avisa al titular si otra persona autorizada canceló su reserva."""
    if actor.pk == reserva.usuario_id:
        return None
    if actor.rol.nombre_rol not in [Rol.Nombre.ADMINISTRADOR, Rol.Nombre.OPERANTE]:
        return None

    horario = reserva.sala_horario.horario
    return Notificacion.objects.create(
        usuario_id=reserva.usuario_id,
        reserva=reserva,
        actor=actor,
        tipo=Notificacion.Tipo.CANCELACION_GESTION,
        mensaje=(
            f"Tu reserva #{reserva.pk} de {reserva.sala_horario.sala.nombre_sala} "
            f"para el {reserva.fecha:%d/%m/%Y}, "
            f"{horario.hora_inicio:%H:%M}-{horario.hora_fin:%H:%M}, "
            f"fue cancelada por un {actor.rol.nombre_rol}."
        ),
        fecha=ahora,
    )


def get_admin_cancellable_reservations(codigo_usuario_admin, now=None):
    """Lista reservas confirmadas que todavía no comenzaron para el administrador."""
    actor = _obtener_usuario_reservante(codigo_usuario_admin)
    if actor.rol.nombre_rol != Rol.Nombre.ADMINISTRADOR:
        raise ReservationError("Solo un administrador puede gestionar cancelaciones.")

    now = now or timezone.localtime()
    reservas = Reserva.objects.filter(
        estado_reserva=Reserva.ESTADO_CONFIRMADA,
        fecha__gte=now.date(),
    ).select_related(
        "usuario", "sala_horario__sala", "sala_horario__horario"
    ).order_by(
        "fecha", "sala_horario__horario__hora_inicio", "id_reserva"
    )
    return [reserva for reserva in reservas if _inicio_de_reserva(reserva) > now]


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
    if (usuario is None or not usuario.password_hash
            or usuario.rol.nombre_rol not in Rol.Nombre.values):
        raise ReservationError("La cuenta no está habilitada para reservar.")
    return usuario


def _obtener_solicitante(codigo_usuario):
    solicitante = Usuario.objects.filter(
        pk=codigo_usuario,
        estado_usuario=True,
        rol__nombre_rol=Rol.Nombre.SOLICITANTE,
    ).first()
    if solicitante is None:
        raise ReservationError("No existe un solicitante activo con ese código.")
    return solicitante


def _validar_actor_sobre_solicitante(actor, solicitante):
    if actor.pk == solicitante.pk:
        return
    if actor.rol.nombre_rol not in [Rol.Nombre.OPERANTE, Rol.Nombre.ADMINISTRADOR]:
        raise ReservationError("No tienes permiso para reservar para otro solicitante.")


def _obtener_reserva_confirmada(id_reserva, bloquear=False):
    consulta = Reserva.objects.select_related(
        "usuario__rol", "sala_horario__sala", "sala_horario__horario"
    )
    if bloquear:
        consulta = consulta.select_for_update()
    try:
        return consulta.get(
            pk=id_reserva, estado_reserva=Reserva.ESTADO_CONFIRMADA
        )
    except Reserva.DoesNotExist as exc:
        raise ReservationError(
            "La reserva no existe o ya no está confirmada."
        ) from exc


def _validar_acceso_reserva(actor, reserva):
    if reserva.usuario_id == actor.pk:
        return
    if actor.rol.nombre_rol not in [Rol.Nombre.OPERANTE, Rol.Nombre.ADMINISTRADOR]:
        raise ReservationError("La reserva no te pertenece.")


def _obtener_reserva_confirmada_del_usuario(usuario, id_reserva, bloquear=False):
    reserva = _obtener_reserva_confirmada(id_reserva, bloquear=bloquear)
    if reserva.usuario_id != usuario.pk:
        raise ReservationError("La reserva no te pertenece.")
    return reserva


def _obtener_reserva_para_cancelar(actor, id_reserva):
    try:
        reserva = Reserva.objects.select_for_update().select_related(
            "usuario", "sala_horario__horario"
        ).get(pk=id_reserva, estado_reserva=Reserva.ESTADO_CONFIRMADA)
    except Reserva.DoesNotExist as exc:
        raise ReservationError(
            "La reserva no existe o ya no está confirmada."
        ) from exc

    _validar_acceso_reserva(actor, reserva)
    return reserva


def _registrar_sancion_por_cancelacion(codigo_usuario, ahora):
    usuario = Usuario.objects.select_for_update().get(pk=codigo_usuario)
    faltas_previas = contar_faltas(usuario, ahora)
    nombre, horas = ESCALA_SANCIONES_CANCELACION[
        min(faltas_previas, len(ESCALA_SANCIONES_CANCELACION) - 1)
    ]
    try:
        tipo_sancion = TipoSancion.objects.get(
            pk=TipoSancion.ID_POR_DURACION[horas], duracion=horas
        )
    except TipoSancion.DoesNotExist as exc:
        raise ReservationError(
            "El catálogo de sanciones está incompleto. Contacta al administrador."
        ) from exc
    return Sancion.objects.create(
        usuario=usuario,
        origen=Sancion.Origen.AUTOMATICA,
        aplicada_por=None,
        tipo_sancion=tipo_sancion,
        motivo=nombre,
        fecha_inicio=ahora,
        fecha_fin=ahora + timedelta(hours=tipo_sancion.duracion),
    )


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


def _puede_cancelar_reserva(reserva, ahora):
    return (
        reserva.estado_reserva == Reserva.ESTADO_CONFIRMADA
        and ahora < _inicio_de_reserva(reserva)
    )


def _cancelacion_es_tardia(reserva, ahora):
    inicio = _inicio_de_reserva(reserva)
    return ahora < inicio and inicio - ahora < ANTICIPACION_CANCELACION_SIN_SANCION


def _validar_dia_habil(fecha):
    if not _es_dia_habilitado(fecha):
        raise ReservationError("Hoy no se realizan reservas: es fin de semana o feriado.")


def _es_dia_habilitado(fecha):
    return fecha.weekday() < 5 and fecha.isoformat() not in settings.RESERVAS_FERIADOS


def _validar_sin_sancion(usuario, ahora):
    sancion = sanciones_vigentes(ahora).filter(
        usuario=usuario
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
        **_construir_notificaciones(codigo_usuario),
    }


def _construir_notificaciones(codigo_usuario):
    if codigo_usuario is None:
        return {"notificaciones": [], "notificaciones_no_leidas": 0}

    notificaciones = Notificacion.objects.filter(
        usuario_id=codigo_usuario, leida=False
    ).select_related("actor", "reserva")
    return {
        "notificaciones": list(notificaciones[:5]),
        "notificaciones_no_leidas": notificaciones.count(),
    }


def mark_notification_as_read(codigo_usuario, id_notificacion):
    """Marca un aviso propio como leído sin eliminarlo del historial."""
    try:
        notificacion = Notificacion.objects.get(
            pk=id_notificacion, usuario_id=codigo_usuario
        )
    except Notificacion.DoesNotExist as exc:
        raise ReservationError("La notificación no existe o no te pertenece.") from exc

    if not notificacion.leida:
        notificacion.leida = True
        notificacion.save(update_fields=["leida"])
    return notificacion


def get_operator_student(codigo_usuario):
    """Obtiene el solicitante que el operante atenderá."""
    return _obtener_solicitante(codigo_usuario)


def get_operator_student_summary(codigo_usuario):
    """Prepara reservas y situación disciplinaria del solicitante seleccionado."""
    solicitante = _obtener_solicitante(codigo_usuario)
    ahora = timezone.localtime()
    reservas = Reserva.objects.filter(
        usuario=solicitante,
        fecha=ahora.date(),
    ).select_related(
        "sala_horario__sala", "sala_horario__horario"
    ).order_by("sala_horario__horario__hora_inicio", "id_reserva")
    sancion_activa = sanciones_vigentes(ahora).filter(
        usuario=solicitante,
    ).order_by("-fecha_fin").first()
    faltas = contar_faltas(solicitante, ahora)
    return {
        "solicitante": solicitante,
        "reservas_solicitante": [
            {
                "reserva": reserva,
                "puede_modificar": _puede_modificar_reserva(reserva, ahora),
                "puede_cancelar": _puede_cancelar_reserva(reserva, ahora),
            }
            for reserva in reservas
        ],
        "sancion_activa": sancion_activa,
        "faltas": min(faltas, len(ESCALA_SANCIONES_CANCELACION)),
    }


def get_operator_availability(codigo_usuario):
    """Reutiliza el cálculo de disponibilidad para reservar a otro solicitante."""
    contexto = get_student_panel(codigo_usuario)
    contexto.pop("mis_reservas", None)
    return contexto


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
            "puede_cancelar": _puede_cancelar_reserva(reserva, ahora),
            "genera_sancion": _cancelacion_es_tardia(reserva, ahora),
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
    return get_reservation_modification_panel_for_actor(codigo_usuario, id_reserva)


def get_reservation_modification_panel_for_actor(codigo_actor, id_reserva):
    """Prepara destinos para una reserva que el actor tiene permiso de modificar."""
    actor = _obtener_usuario_reservante(codigo_actor)
    reserva = _obtener_reserva_confirmada(id_reserva)
    _validar_acceso_reserva(actor, reserva)
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


class ScheduleNotBlockedError(Exception):
    """Ese sala_horario no está en estado MANTENIMIENTO."""


class MaintenanceAlreadyStartedError(Exception):
    """La franja ya comenzó y su mantenimiento no puede modificarse."""


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


def get_active_maintenance_blocks():
    """Devuelve solo los horarios que actualmente siguen en mantenimiento."""
    activos = []
    sala_horarios = SalaHorario.objects.filter(
        estado_sala_horario=SalaHorario.ESTADO_MANTENIMIENTO
    ).select_related("sala", "horario").order_by(
        "sala__nombre_sala", "horario__hora_inicio"
    )

    for sala_horario in sala_horarios:
        ultimo_bloqueo = Bloqueo.objects.filter(
            sala_horario=sala_horario,
            desbloqueo__isnull=True,
        ).select_related("usuario", "sala_horario__horario").order_by(
            "-fecha", "-id_bloqueo"
        ).first()
        activos.append(
            {
                "sala_horario": sala_horario,
                "bloqueo": ultimo_bloqueo,
                "puede_desbloquear": (
                    ultimo_bloqueo is not None
                    and can_unblock_maintenance(ultimo_bloqueo)
                ),
            }
        )

    return activos


# --- Caso de uso RES-CU-02 --------------------------------------------------

@transaction.atomic
def block_room_schedule_for_maintenance(codigo_usuario_admin, id_sala_horario, motivo):
    """
    Bloquea por mantenimiento una combinación sala+horario.

    Lanza NotAuthorizedError (E1), ScheduleNotFoundError (E2) o
    ScheduleAlreadyBlockedError si el sistema debe rechazar la operación.
    """
    # Administradores y operantes pueden gestionar mantenimiento.
    if not _puede_gestionar_mantenimiento(codigo_usuario_admin):
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

    ahora = timezone.localtime()
    if not can_block_maintenance(sala_horario, ahora):
        raise MaintenanceAlreadyStartedError(
            "El horario ya comenzó y no puede bloquearse por mantenimiento."
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
    Auditoria.objects.bulk_create([
        Auditoria(
            reserva=reserva, actor_id=codigo_usuario_admin,
            accion=Auditoria.Accion.CANCELAR,
        )
        for reserva in reservas_canceladas
    ])
    Notificacion.objects.bulk_create([
        Notificacion(
            usuario_id=reserva.usuario_id,
            reserva=reserva,
            actor_id=codigo_usuario_admin,
            tipo=Notificacion.Tipo.MANTENIMIENTO,
            mensaje=(
                f"Tu reserva #{reserva.pk} de {sala_horario.sala.nombre_sala} "
                f"para el {reserva.fecha:%d/%m/%Y}, "
                f"{sala_horario.horario.hora_inicio:%H:%M}-"
                f"{sala_horario.horario.hora_fin:%H:%M}, fue cancelada por "
                f"mantenimiento. Motivo: {motivo}"
            ),
            fecha=ahora,
        )
        for reserva in reservas_canceladas
    ])

    # Paso 6 — el horario de la sala pasa a MANTENIMIENTO
    sala_horario.estado_sala_horario = SalaHorario.ESTADO_MANTENIMIENTO
    sala_horario.save(update_fields=["estado_sala_horario"])

    # Paso 7 — registrar el bloqueo (quién, motivo, cuándo)
    Bloqueo.objects.create(
        usuario_id=codigo_usuario_admin,
        sala_horario=sala_horario,
        motivo=motivo,
        fecha=ahora,
    )

    # Paso 8 — confirmar el resultado
    return {
        "sala_horario": sala_horario,
        "reservas_canceladas": reservas_canceladas,
    }


@transaction.atomic
def unblock_room_schedule_from_maintenance(
    codigo_usuario_admin, id_sala_horario
):
    """Vuelve a habilitar un horario en mantenimiento sin alterar su historial."""
    if not _puede_gestionar_mantenimiento(codigo_usuario_admin):
        raise NotAuthorizedError(
            "No tienes permisos para habilitar salas. Contacta al administrador."
        )

    try:
        sala_horario = SalaHorario.objects.select_for_update().select_related(
            "sala", "horario"
        ).get(pk=id_sala_horario)
    except SalaHorario.DoesNotExist as exc:
        raise ScheduleNotFoundError(
            f"No existe una combinación de sala y horario con id {id_sala_horario}."
        ) from exc

    if sala_horario.estado_sala_horario != SalaHorario.ESTADO_MANTENIMIENTO:
        raise ScheduleNotBlockedError(
            f"El horario {sala_horario.horario} de la sala "
            f"{sala_horario.sala} no está en mantenimiento."
        )

    bloqueo = Bloqueo.objects.select_for_update().filter(
        sala_horario=sala_horario,
        desbloqueo__isnull=True,
    ).order_by("-fecha", "-id_bloqueo").first()
    if bloqueo is None:
        raise ScheduleNotBlockedError(
            "No existe un bloqueo activo que se pueda retirar."
        )
    if not can_unblock_maintenance(bloqueo):
        raise MaintenanceAlreadyStartedError(
            "El mantenimiento ya comenzó y no puede desbloquearse."
        )

    sala_horario.estado_sala_horario = SalaHorario.ESTADO_DISPONIBLE
    sala_horario.save(update_fields=["estado_sala_horario"])
    Desbloqueo.objects.create(
        bloqueo=bloqueo,
        desbloqueado_por_id=codigo_usuario_admin,
        fecha_desbloqueo=timezone.localtime(),
    )
    return sala_horario


def _maintenance_start(sala_horario, fecha):
    return timezone.make_aware(
        datetime.combine(fecha, sala_horario.horario.hora_inicio),
        timezone.get_current_timezone(),
    )


def can_block_maintenance(sala_horario, now=None):
    """Impide crear mantenimiento para una franja de hoy que ya comenzó."""
    if not RESTRINGIR_BLOQUEO_TRAS_INICIO:
        return True
    now = now or timezone.localtime()
    return now < _maintenance_start(sala_horario, now.date())


def can_unblock_maintenance(bloqueo, now=None):
    """Indica si el bloqueo puede retirarse antes del inicio del mantenimiento."""
    if not RESTRINGIR_DESBLOQUEO_TRAS_INICIO:
        return True
    now = now or timezone.localtime()
    fecha_bloqueo = timezone.localtime(bloqueo.fecha).date()
    return now < _maintenance_start(bloqueo.sala_horario, fecha_bloqueo)


def _puede_gestionar_mantenimiento(codigo_usuario):
    return Usuario.objects.filter(
        pk=codigo_usuario,
        estado_usuario=True,
        rol__nombre_rol__in=[ROL_ADMINISTRADOR, ROL_OPERANTE],
    ).exists()
