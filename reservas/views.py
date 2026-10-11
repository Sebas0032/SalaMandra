"""
Vistas de SalaMandra.

Un único caso de uso en esta etapa (Sesión 07, RES-CU-02): un Administrador
inicia sesión, ve las salas/horarios/reservas/bloqueos y puede bloquear un
horario de una sala por mantenimiento.

El login se implementó a mano (no usa django.contrib.auth) para respetar
las tablas del equipo (`usuarios`, `roles`, `usuarios_roles`). La sesión se
guarda en una cookie firmada (ver SESSION_ENGINE en settings.py).
"""

from functools import wraps

from django.contrib import messages
from django.db import OperationalError, ProgrammingError
from django.shortcuts import redirect, render

from . import services


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


def admin_login_required(view_func):
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

@handle_db_errors
def login_view(request):
    if request.session.get("codigo_usuario"):
        return redirect("dashboard")

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        usuario = services.authenticate_admin(email, password)

        if usuario:
            request.session["codigo_usuario"] = usuario.codigo_usuario
            request.session["nombre_completo"] = str(usuario)
            messages.success(request, f"Bienvenido/a, {usuario.nombre}.")
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
@handle_db_errors
def dashboard_view(request):
    context = {
        "nombre_completo": request.session.get("nombre_completo"),
        "sala_horarios": services.get_sala_horarios(),
        "reservas": services.get_reservas(),
        "bloqueos": services.get_bloqueos(),
    }
    return render(request, "reservas/dashboard.html", context)


@admin_login_required
@handle_db_errors
def block_room_view(request):
    if request.method != "POST":
        return redirect("dashboard")

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
