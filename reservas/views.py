"""Vistas del panel y del bloqueo de horarios por mantenimiento."""

from functools import wraps
from urllib.parse import urlencode

from django.contrib import messages
from django.db import IntegrityError, OperationalError, ProgrammingError
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from cuentas.permisos import admin_login_required, login_required, operante_login_required
from cuentas.services import usuario_tiene_rol

from . import services, gestion_salas, gestion_sanciones
from .models import Reserva, Rol, Sala, SalaHorario


# --- Decoradores de ayuda ----------------------------------------------------

def handle_db_errors(view_func):
    """Si la base de datos falla (por ejemplo, faltan las tablas), muestra una página
    explicativa en vez de un error 500."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except (OperationalError, ProgrammingError) as exc:
            return render(
                request, "reservas/db_error.html", {"error": str(exc)}, status=503
            )

    return wrapper


# --- Vistas ------------------------------------------------------------------

@handle_db_errors
@login_required
def student_panel_view(request):
    """Muestra el panel y procesa las solicitudes de reserva del estudiante."""
    if request.method == "POST":
        reserva = _intentar_crear_reserva(request)
        if reserva is not None:
            messages.success(request, f"Reserva #{reserva.pk} confirmada.")
        return redirect("student_panel")

    return render(
        request,
        "reservas/panel_solicitante.html",
        _construir_contexto_panel_solicitante(request),
    )


@handle_db_errors
@login_required
def modify_reservation_view(request, id_reserva):
    """Muestra y procesa el cambio de sala y horario de una reserva propia."""
    if request.method == "POST":
        reserva = _intentar_modificar_reserva(request, id_reserva)
        if reserva is not None:
            messages.success(
                request, f"Reserva #{reserva.pk} modificada correctamente."
            )
            return redirect("student_panel")
        return redirect("modify_reservation", id_reserva=id_reserva)

    try:
        contexto = services.get_reservation_modification_panel(
            request.usuario.pk, id_reserva
        )
    except services.ReservationError as exc:
        messages.error(request, str(exc))
        return redirect("student_panel")

    contexto.update(
        {
            "usuario": request.usuario,
            "es_admin": usuario_tiene_rol(
                request.usuario.pk, "Administrador"
            ),
        }
    )
    return render(request, "reservas/modificar_reserva.html", contexto)


@handle_db_errors
@login_required
@require_POST
def cancel_reservation_view(request, id_reserva):
    """Cancela una reserva y comunica si se aplicó una sanción."""
    try:
        resultado = services.cancel_reservation(request.usuario.pk, id_reserva)
    except services.ReservationError as exc:
        messages.error(request, str(exc))
    else:
        _mostrar_resultado_cancelacion(request, resultado)
    return redirect("student_panel")


@handle_db_errors
@admin_login_required
def admin_cancellations_view(request):
    """Muestra las reservas activas que el administrador todavía puede cancelar."""
    reservas = services.get_admin_cancellable_reservations(request.usuario.pk)
    return render(
        request,
        "reservas/gestion_cancelaciones.html",
        {
            "reservas": reservas,
            "nombre_completo": request.session.get("nombre_completo"),
        },
    )


@handle_db_errors
@admin_login_required
@require_POST
def admin_cancel_reservation_view(request, id_reserva):
    """Cancela por decisión administrativa sin sancionar al solicitante."""
    try:
        resultado = services.cancel_reservation(request.usuario.pk, id_reserva)
    except services.ReservationError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(
            request,
            f"Reserva #{resultado['reserva'].pk} cancelada administrativamente "
            "sin sanción.",
        )
    return redirect("admin_cancellations")


def _mostrar_resultado_cancelacion(request, resultado):
    reserva = resultado["reserva"]
    sancion = resultado["sancion"]
    if sancion is None:
        messages.success(request, f"Reserva #{reserva.pk} cancelada sin sanción.")
        return
    vence = timezone.localtime(sancion.fecha_fin).strftime("%d/%m/%Y %H:%M")
    messages.success(
        request,
        f"Reserva #{reserva.pk} cancelada. Se aplicó {sancion.tipo_sancion} "
        f"hasta el {vence}.",
    )


def _intentar_crear_reserva(request):
    """Procesa el formulario y traduce rechazos a mensajes para la interfaz."""
    try:
        id_sala_horario = _leer_id_sala_horario(request)
        return services.create_student_reservation(
            request.usuario.pk,
            id_sala_horario,
            request.POST.get("actividad", ""),
        )
    except ValueError:
        messages.error(request, "Selecciona una sala y un horario.")
    except services.ReservationError as exc:
        messages.error(request, str(exc))
    except IntegrityError:
        messages.error(
            request,
            "El bloque ya fue reservado por otro usuario. Elige otro horario disponible.",
        )
    except OperationalError as exc:
        if "locked" not in str(exc).lower():
            raise
        messages.error(
            request,
            "El sistema está atendiendo otra solicitud. Vuelve a intentarlo.",
        )
    return None


def _intentar_modificar_reserva(request, id_reserva):
    """Solicita el cambio y comunica cualquier rechazo sin perder la original."""
    try:
        return services.modify_student_reservation(
            request.usuario.pk,
            id_reserva,
            _leer_id_sala_horario(request),
        )
    except ValueError:
        messages.error(request, "Selecciona una sala y un horario.")
    except services.ReservationError as exc:
        messages.error(request, str(exc))
    except IntegrityError:
        messages.error(
            request,
            "El bloque ya fue reservado por otro usuario. "
            "La reserva original se conserva sin cambios.",
        )
    except OperationalError as exc:
        if "locked" not in str(exc).lower():
            raise
        messages.error(
            request,
            "El sistema está atendiendo otra solicitud. Vuelve a intentarlo.",
        )
    return None


def _leer_id_sala_horario(request):
    id_sala_horario = int(request.POST.get("id_sala_horario", ""))
    if not 0 < id_sala_horario <= 9223372036854775807:
        raise ValueError
    return id_sala_horario


def _construir_contexto_panel_solicitante(request):
    return {
        **services.get_student_panel(request.usuario.pk),
        "usuario": request.usuario,
        "es_admin": usuario_tiene_rol(request.usuario.pk, "Administrador"),
    }

@login_required
@handle_db_errors
def dashboard_view(request):
    if usuario_tiene_rol(request.usuario.pk, Rol.Nombre.OPERANTE):
        return redirect("operator_panel")
    if not usuario_tiene_rol(request.usuario.pk, "Administrador"):
        return redirect("student_panel")
    context = _construir_contexto_mantenimiento(request)
    return render(request, "reservas/dashboard.html", context)


def _construir_contexto_mantenimiento(request):
    combinaciones = list(services.get_sala_horarios())
    ahora = timezone.localtime()
    for combinacion in combinaciones:
        combinacion.puede_bloquear = services.can_block_maintenance(
            combinacion, ahora
        )
    horarios = sorted({sh.horario_id: sh.horario for sh in combinaciones}.values(), key=lambda h: h.hora_inicio)
    ocupados = set(services.get_reservas().filter(
        fecha=timezone.localdate(), estado_reserva__in=services.ESTADOS_ACTIVOS
    ).values_list("sala_horario_id", flat=True))
    salas = {}
    for sh in combinaciones:
        salas.setdefault(sh.sala_id, {"sala": sh.sala, "horarios": {}})["horarios"][sh.horario_id] = sh
    filas = []
    for fila in salas.values():
        celdas = []
        for horario in horarios:
            sh = fila["horarios"].get(horario.pk)
            estado = "Sin horario"
            if sh:
                if sh.estado_sala_horario == "MANTENIMIENTO":
                    estado = "Mantenimiento"
                elif sh.pk in ocupados:
                    estado = "Reservado"
                elif sh.estado_sala_horario == "DISPONIBLE" and sh.sala.estado_sala:
                    estado = "Disponible"
                else:
                    estado = "No disponible"
            celdas.append(estado)
        filas.append({"sala": fila["sala"], "estados": celdas})
    return {
        "horarios": horarios, "filas": filas, "hoy": timezone.localdate(),
        "nombre_completo": request.session.get("nombre_completo"),
        "sala_horarios": combinaciones,
        "reservas": services.get_reservas(),
        "bloqueos": services.get_bloqueos(),
        "bloqueos_activos": services.get_active_maintenance_blocks(),
    }


@admin_login_required
@handle_db_errors
def block_room_view(request):
    if request.method != "POST":
        return dashboard_view(request)

    _procesar_bloqueo_mantenimiento(request)
    return redirect("dashboard")


def _procesar_bloqueo_mantenimiento(request):
    motivo = request.POST.get("motivo", "").strip()
    id_raw = request.POST.get("id_sala_horario", "").strip()
    if not id_raw or not motivo:
        messages.error(
            request, "Selecciona una sala/horario y escribe un motivo para el bloqueo."
        )
        return None
    if len(motivo) > 200:
        messages.error(request, "El motivo no puede superar los 200 caracteres.")
        return None
    try:
        id_sala_horario = int(id_raw)
    except ValueError:
        messages.error(request, "La sala/horario seleccionado no es válido.")
        return None
    try:
        resultado = services.block_room_schedule_for_maintenance(
            codigo_usuario_admin=request.usuario.pk,
            id_sala_horario=id_sala_horario,
            motivo=motivo,
        )
    except (
        services.ScheduleNotFoundError,
        services.ScheduleAlreadyBlockedError,
        services.MaintenanceAlreadyStartedError,
        services.NotAuthorizedError,
    ) as exc:
        messages.error(request, str(exc))
        return None
    sh = resultado["sala_horario"]
    canceladas = resultado["reservas_canceladas"]
    base = f"Horario {sh.horario} de {sh.sala} bloqueado por mantenimiento."
    extra = (
        f" {len(canceladas)} reserva(s) pasaron a POR_MANTENIMIENTO (sin penalización)."
        if canceladas else " No había reservas asociadas."
    )
    messages.success(request, base + extra)
    return resultado


@admin_login_required
@handle_db_errors
@require_POST
def unblock_room_view(request, id_sala_horario):
    """Saca un horario de mantenimiento y lo vuelve a dejar disponible."""
    try:
        sala_horario = services.unblock_room_schedule_from_maintenance(
            codigo_usuario_admin=request.session["codigo_usuario"],
            id_sala_horario=id_sala_horario,
        )
    except (
        services.ScheduleNotFoundError,
        services.ScheduleNotBlockedError,
        services.MaintenanceAlreadyStartedError,
        services.NotAuthorizedError,
    ) as exc:
        messages.error(request, str(exc))
    else:
        messages.success(
            request,
            f"El horario {sala_horario.horario} de {sala_horario.sala} "
            "volvió a estar disponible. Las reservas afectadas anteriormente "
            "no fueron restauradas.",
        )

    return redirect("dashboard")


# --- Panel del Operante ------------------------------------------------------

@handle_db_errors
@operante_login_required
def operator_panel_view(request):
    accion = request.POST.get("accion") or request.GET.get("accion", "reservar")
    if accion not in {"reservar", "modificar", "cancelar", "mantenimiento"}:
        accion = "reservar"
    if request.method == "POST":
        return _procesar_accion_operante(request, accion)
    return render(
        request,
        "reservas/panel_operante.html",
        _construir_contexto_operante(request, accion),
    )


def _procesar_accion_operante(request, accion):
    codigo = request.POST.get("codigo_solicitante", "").strip()
    if accion == "mantenimiento":
        _procesar_bloqueo_mantenimiento(request)
        return redirect(_url_operante(accion))
    try:
        codigo_solicitante = _validar_codigo_operante(codigo)
        if accion == "reservar":
            reserva = services.create_reservation(
                request.usuario.pk,
                codigo_solicitante,
                _leer_id_sala_horario(request),
                request.POST.get("actividad", ""),
            )
            messages.success(
                request,
                f"Reserva #{reserva.pk} creada para {reserva.usuario}."
            )
        else:
            id_reserva = _leer_id_reserva_operante(request, codigo_solicitante)
            if accion == "modificar":
                reserva = services.modify_reservation(
                    request.usuario.pk,
                    id_reserva,
                    _leer_id_sala_horario(request),
                )
                messages.success(
                    request, f"Reserva #{reserva.pk} modificada correctamente."
                )
            else:
                resultado = services.cancel_reservation(request.usuario.pk, id_reserva)
                _mostrar_resultado_cancelacion(request, resultado)
    except (ValueError, services.ReservationError) as exc:
        mensaje = str(exc) or "Selecciona una reserva, sala y horario válidos."
        messages.error(request, mensaje)
    except IntegrityError:
        messages.error(
            request,
            "El horario ya fue reservado. Selecciona otro bloque disponible.",
        )
    return redirect(_url_operante(accion, codigo))


def _construir_contexto_operante(request, accion):
    contexto = {
        "accion": accion,
        "usuario": request.usuario,
        "nombre_completo": request.session.get("nombre_completo"),
    }
    if accion == "mantenimiento":
        contexto.update(_construir_contexto_mantenimiento(request))
        return contexto

    codigo = request.GET.get("codigo", "").strip()
    contexto["codigo_buscado"] = codigo
    if not codigo:
        return contexto
    try:
        codigo_solicitante = _validar_codigo_operante(codigo)
        contexto.update(services.get_operator_student_summary(codigo_solicitante))
        contexto.update(services.get_operator_availability(codigo_solicitante))
        id_reserva = request.GET.get("reserva", "").strip()
        if id_reserva:
            reserva_id = int(id_reserva)
            if not Reserva.objects.filter(
                pk=reserva_id, usuario_id=codigo_solicitante
            ).exists():
                raise services.ReservationError(
                    "La reserva seleccionada no pertenece al solicitante."
                )
            contexto["reserva_seleccionada"] = Reserva.objects.select_related(
                "sala_horario__sala", "sala_horario__horario"
            ).get(pk=reserva_id)
            if accion == "modificar":
                contexto.update(
                    services.get_reservation_modification_panel_for_actor(
                        request.usuario.pk, reserva_id
                    )
                )
    except (ValueError, services.ReservationError) as exc:
        contexto["error_busqueda"] = str(exc) or "Ingresa un código válido."
    return contexto


def _validar_codigo_operante(codigo):
    if not codigo.isascii() or not codigo.isdecimal():
        raise services.ReservationError("Ingresa un código de solicitante válido.")
    valor = int(codigo)
    if not 0 < valor <= 9223372036854775807:
        raise services.ReservationError("Ingresa un código de solicitante válido.")
    services.get_operator_student(valor)
    return valor


def _leer_id_reserva_operante(request, codigo_solicitante):
    id_reserva = int(request.POST.get("id_reserva", ""))
    if not Reserva.objects.filter(
        pk=id_reserva, usuario_id=codigo_solicitante
    ).exists():
        raise services.ReservationError(
            "La reserva seleccionada no pertenece al solicitante."
        )
    return id_reserva


def _url_operante(accion, codigo="", reserva=""):
    parametros = {"accion": accion}
    if codigo:
        parametros["codigo"] = codigo
    if reserva:
        parametros["reserva"] = reserva
    return f"{reverse('operator_panel')}?{urlencode(parametros)}"


@handle_db_errors
@operante_login_required
@require_POST
def operator_unblock_room_view(request, id_sala_horario):
    try:
        services.unblock_room_schedule_from_maintenance(
            request.usuario.pk, id_sala_horario
        )
    except (
        services.ScheduleNotFoundError,
        services.ScheduleNotBlockedError,
        services.MaintenanceAlreadyStartedError,
        services.NotAuthorizedError,
    ) as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "El horario volvió a estar disponible.")
    return redirect(_url_operante("mantenimiento"))

# En esta parte se encuentra para poder CREAR tanto SALAS y HORARIOS por el admin
@handle_db_errors
@admin_login_required
def gestion_salas_view(request):
    """Página exclusiva del Administrador para dar de alta salas y horarios."""
    if request.method == "POST":
        _procesar_alta_sala_o_horario(request)
        return redirect("gestion_salas")

    return render(request, "reservas/gestion_salas.html", _contexto_gestion_salas(request))


def _procesar_alta_sala_o_horario(request):
    """Recibe el formulario; la lógica y sus validaciones viven en gestion_salas.py."""
    accion = request.POST.get("accion", "")
    try:
        if accion == "crear_sala":
            sala = gestion_salas.create_room(
                request.usuario.pk, request.POST.get("nombre_sala", "")
            )
            messages.success(request, f"Se creó la sala {sala.nombre_sala}.")
        elif accion == "crear_horario":
            asignacion = gestion_salas.create_room_schedule(
                request.usuario.pk,
                request.POST.get("id_sala", ""),
                request.POST.get("hora_inicio", ""),
                request.POST.get("hora_fin", ""),
            )
            messages.success(
                request, f"Horario {asignacion.horario} asignado a {asignacion.sala}."
            )
        else:
            messages.error(request, "Acción no reconocida.")
    except gestion_salas.GestionSalasError as exc:
        messages.error(request, str(exc))
    except IntegrityError:
        messages.error(request, "La sala o el horario ya existen. Actualiza la página.")


def _contexto_gestion_salas(request):
    return {
        "nombre_completo": request.session.get("nombre_completo"),
        "salas": Sala.objects.all().order_by("nombre_sala"),
        "salas_activas": Sala.objects.filter(estado_sala=True).order_by("nombre_sala"),
        "asignaciones": SalaHorario.objects.select_related("sala", "horario").order_by(
            "sala__nombre_sala", "horario__hora_inicio"
        ),
    }


# --- Administración de sanciones y solicitantes ----------------------------

@handle_db_errors
@admin_login_required
def sanctions_admin_view(request):
    """Lista solicitantes, sanciones vigentes y estado de sus cuentas."""
    filtro = request.GET.get("filtro", "todos")
    if filtro not in {"todos", "activos", "inactivos", "sancionados"}:
        filtro = "todos"
    termino = request.GET.get("q", "").strip()
    return render(
        request,
        "reservas/gestion_sanciones.html",
        {
            "nombre_completo": request.session.get("nombre_completo"),
            "filas": gestion_sanciones.get_solicitantes(termino, filtro),
            "opciones_duracion": gestion_sanciones.OPCIONES_DURACION,
            "filtro": filtro,
            "termino": termino,
            "codigo_seleccionado": request.GET.get("codigo", ""),
        },
    )


@handle_db_errors
@admin_login_required
@require_POST
def apply_sanction_view(request):
    try:
        sancion = gestion_sanciones.apply_manual_sanction(
            request.usuario.pk,
            _leer_codigo_solicitante(request),
            request.POST.get("duracion", ""),
            request.POST.get("motivo", ""),
        )
    except gestion_sanciones.GestionSancionesError as exc:
        messages.error(request, str(exc))
    else:
        vence = timezone.localtime(sancion.fecha_fin).strftime(
            "%d/%m/%Y %H:%M"
        )
        messages.success(
            request,
            f"Sanción aplicada a {sancion.usuario}. Vigente hasta {vence}.",
        )
    return redirect("sanctions_admin")


@handle_db_errors
@admin_login_required
@require_POST
def clear_sanctions_view(request):
    try:
        cantidad = gestion_sanciones.clear_all_sanctions(request.usuario.pk)
    except gestion_sanciones.GestionSancionesError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(
            request,
            f"Reinicio semestral completado: {cantidad} sanción(es) eliminada(s).",
        )
    return redirect("sanctions_admin")


@handle_db_errors
@admin_login_required
@require_POST
def change_student_status_view(request, codigo_usuario):
    nuevo_estado = request.POST.get("nuevo_estado", "")
    if nuevo_estado not in {"0", "1"}:
        messages.error(request, "El estado solicitado no es válido.")
        return redirect("sanctions_admin")
    try:
        solicitante = gestion_sanciones.set_student_active_status(
            request.usuario.pk,
            codigo_usuario,
            activo=nuevo_estado == "1",
        )
    except gestion_sanciones.GestionSancionesError as exc:
        messages.error(request, str(exc))
    else:
        estado = "activada" if solicitante.estado_usuario else "desactivada"
        messages.success(request, f"Cuenta de {solicitante} {estado}.")
    return redirect("sanctions_admin")


def _leer_codigo_solicitante(request):
    codigo = request.POST.get("codigo_solicitante", "").strip()
    if not codigo.isascii() or not codigo.isdecimal():
        raise gestion_sanciones.GestionSancionesError(
            "Ingresa un código universitario válido."
        )
    valor = int(codigo)
    if not 0 < valor <= 9223372036854775807:
        raise gestion_sanciones.GestionSancionesError(
            "Ingresa un código universitario válido."
        )
    return valor
