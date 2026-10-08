"""
Vistas de SalaMandra.

Hay un único caso de uso en esta etapa (Sesión 07, RES-CU-02): un
Administrador inicia sesión, ve las salas/horarios/reservas/bloqueos
existentes, y puede bloquear una combinación sala+horario por
mantenimiento.

El login NO usa django.contrib.auth (ese módulo depende del ORM de
Django). En cambio:
    - Las credenciales viven en MongoDB (colección `usuarios`, con el
      rol Administrador asignado vía `usuarios_roles` + `roles`).
    - La sesión iniciada se guarda con las sesiones de Django
      configuradas en modo "signed_cookies" (ver settings.py), que no
      requieren base de datos relacional.
"""

from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect, render
from pymongo.errors import PyMongoError

from . import services


# --- Decoradores de ayuda ----------------------------------------------------

def handle_mongo_errors(view_func):
    """Si MongoDB no responde, muestra una página clara en vez de un error 500."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except PyMongoError as exc:
            return render(
                request,
                "reservas/mongo_error.html",
                {"error": str(exc)},
                status=503,
            )

    return wrapper


def admin_login_required(view_func):
    """Equivalente casero a @login_required, sin usar django.contrib.auth."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("codigo_usuario"):
            messages.error(
                request, "Debes iniciar sesión como Administrador para continuar."
            )
            return redirect("login")
        return view_func(request, *args, **kwargs)

    return wrapper


# --- Vistas ------------------------------------------------------------------

@handle_mongo_errors
def login_view(request):
    if request.session.get("codigo_usuario"):
        return redirect("dashboard")

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        usuario = services.authenticate_admin(email, password)

        if usuario:
            request.session["codigo_usuario"] = usuario["codigo_usuario"]
            request.session["nombre_completo"] = (
                f"{usuario['nombre']} {usuario['apellido']}"
            )
            messages.success(request, f"Bienvenido/a, {usuario['nombre']}.")
            return redirect("dashboard")

        messages.error(
            request,
            "Correo o contraseña incorrectos, o el usuario no tiene rol de "
            "Administrador.",
        )

    return render(request, "reservas/login.html")


def logout_view(request):
    request.session.flush()
    messages.success(request, "Sesión cerrada correctamente.")
    return redirect("login")


@admin_login_required
@handle_mongo_errors
def dashboard_view(request):
    context = {
        "nombre_completo": request.session.get("nombre_completo"),
        "salas": services.get_salas(),
        "horarios": services.get_horarios(),
        "sala_horarios": services.get_sala_horarios_con_detalle(),
        "reservas": services.get_reservas_con_detalle(),
        "bloqueos": services.get_bloqueos_con_detalle(),
    }
    return render(request, "reservas/dashboard.html", context)


@admin_login_required
@handle_mongo_errors
def block_room_view(request):
    if request.method != "POST":
        return redirect("dashboard")

    motivo = request.POST.get("motivo", "").strip()
    id_sala_horario_raw = request.POST.get("id_sala_horario", "").strip()

    if not id_sala_horario_raw or not motivo:
        messages.error(
            request,
            "Selecciona una sala/horario y escribe un motivo para el bloqueo.",
        )
        return redirect("dashboard")

    try:
        id_sala_horario = int(id_sala_horario_raw)
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

    sala = resultado["sala"]
    horario = resultado["horario"]
    canceladas = resultado["reservas_canceladas"]

    if canceladas:
        messages.success(
            request,
            f"Horario {horario['hora_inicio']}-{horario['hora_fin']} de "
            f"{sala['nombre_sala']} bloqueado por mantenimiento. "
            f"{len(canceladas)} reserva(s) pasaron a POR_MANTENIMIENTO "
            "(sin penalización).",
        )
    else:
        messages.success(
            request,
            f"Horario {horario['hora_inicio']}-{horario['hora_fin']} de "
            f"{sala['nombre_sala']} bloqueado por mantenimiento. No había "
            "reservas asociadas.",
        )

    return redirect("dashboard")
