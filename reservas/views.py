"""Vistas del panel y del bloqueo de horarios por mantenimiento."""

from functools import wraps

from django.contrib import messages
from django.db import IntegrityError, OperationalError, ProgrammingError
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from cuentas.permisos import admin_login_required, login_required
from cuentas.services import usuario_tiene_rol

from . import services, gestion_salas
from .models import Sala, SalaHorario


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
    if not usuario_tiene_rol(request.usuario.pk, "Administrador"):
        return redirect("student_panel")
    combinaciones = list(services.get_sala_horarios())
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
    context = {
        "horarios": horarios, "filas": filas, "hoy": timezone.localdate(),
        "nombre_completo": request.session.get("nombre_completo"),
        "sala_horarios": combinaciones,
        "reservas": services.get_reservas(),
        "bloqueos": services.get_bloqueos(),
    }
    return render(request, "reservas/dashboard.html", context)


@admin_login_required
@handle_db_errors
def block_room_view(request):
    if request.method != "POST":
        return dashboard_view(request)

    motivo = request.POST.get("motivo", "").strip()
    id_raw = request.POST.get("id_sala_horario", "").strip()

    if not id_raw or not motivo:
        messages.error(
            request, "Selecciona una sala/horario y escribe un motivo para el bloqueo."
        )
        return redirect("dashboard")

    if len(motivo) > 200:
        messages.error(request, "El motivo no puede superar los 200 caracteres.")
        return redirect("dashboard")

    try:
        id_sala_horario = int(id_raw)
    except ValueError:
        messages.error(request, "La sala/horario seleccionado no es válido.")
        return redirect("dashboard")

    try:
        resultado = services.block_room_schedule_for_maintenance(
            codigo_usuario_admin=request.session["codigo_usuario"],
            id_sala_horario=id_sala_horario,
            motivo=motivo,
        )
    except (
        services.ScheduleNotFoundError,
        services.ScheduleAlreadyBlockedError,
        services.NotAuthorizedError,
    ) as exc:
        messages.error(request, str(exc))
        return redirect("dashboard")

    sh = resultado["sala_horario"]
    canceladas = resultado["reservas_canceladas"]
    base = f"Horario {sh.horario} de {sh.sala} bloqueado por mantenimiento."

    if canceladas:
        messages.success(
            request,
            f"{base} {len(canceladas)} reserva(s) pasaron a POR_MANTENIMIENTO "
            "(sin penalización).",
        )
    else:
        messages.success(request, f"{base} No había reservas asociadas.")

    return redirect("dashboard")

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
