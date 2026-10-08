"""
Vistas de SalaMandra.

Hay un único caso de uso en esta etapa (Sesión 07, RES-CU-02): un
Administrador inicia sesión, ve las salas/reservas/bloqueos existentes,
y puede bloquear el horario de una sala por mantenimiento.

El "login de Administrador" NO usa django.contrib.auth (ese módulo
depende del ORM de Django). En cambio:
    - Las credenciales del Administrador viven en MongoDB
      (colección `admins`, ver management/commands/seed_data.py).
    - La sesión iniciada se guarda con las sesiones de Django
      configuradas en modo "signed_cookies" (ver settings.py),
      que no requieren base de datos relacional.
"""

from functools import wraps

from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.shortcuts import redirect, render
from pymongo.errors import PyMongoError

from . import services
from .mongo import get_db


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
        if not request.session.get("admin_username"):
            messages.error(
                request, "Debes iniciar sesión como Administrador para continuar."
            )
            return redirect("login")
        return view_func(request, *args, **kwargs)

    return wrapper


# --- Vistas ------------------------------------------------------------------

@handle_mongo_errors
def login_view(request):
    if request.session.get("admin_username"):
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        db = get_db()
        admin = db.admins.find_one({"username": username})

        if admin and check_password(password, admin["password_hash"]):
            request.session["admin_username"] = username
            messages.success(request, f"Bienvenido/a, {username}.")
            return redirect("dashboard")

        messages.error(request, "Usuario o contraseña incorrectos.")

    return render(request, "reservas/login.html")


def logout_view(request):
    request.session.flush()
    messages.success(request, "Sesión cerrada correctamente.")
    return redirect("login")


@admin_login_required
@handle_mongo_errors
def dashboard_view(request):
    rooms = services.get_rooms()
    reservations = services.get_reservations()
    bloqueos = services.get_bloqueos()

    reservas_por_sala = {}
    for reserva in reservations:
        reservas_por_sala.setdefault(reserva["room_id"], []).append(reserva)

    context = {
        "admin_username": request.session.get("admin_username"),
        "rooms": rooms,
        "reservas_por_sala": reservas_por_sala,
        "bloqueos": bloqueos,
    }
    return render(request, "reservas/dashboard.html", context)


@admin_login_required
@handle_mongo_errors
def block_room_view(request):
    if request.method != "POST":
        return redirect("dashboard")

    room_id = request.POST.get("room_id", "").strip()
    start = request.POST.get("start", "").strip()
    end = request.POST.get("end", "").strip()
    motivo = request.POST.get("motivo", "").strip()

    if not room_id or not start or not end or not motivo:
        messages.error(
            request,
            "Todos los campos son obligatorios: sala, hora de inicio, "
            "hora de fin y motivo.",
        )
        return redirect("dashboard")

    try:
        resultado = services.block_room_schedule_for_maintenance(
            is_admin=True,  # ya lo garantizó @admin_login_required
            room_id=room_id,
            start=start,
            end=end,
            motivo=motivo,
        )
    except (
        services.RoomNotFoundError,
        services.ScheduleAlreadyBlockedError,
        services.NotAuthorizedError,
    ) as exc:
        messages.error(request, str(exc))
        return redirect("dashboard")

    reserva_cancelada = resultado["reserva_cancelada"]
    if reserva_cancelada:
        quien = reserva_cancelada.get(
            "student_name", reserva_cancelada.get("student_code", "un estudiante")
        )
        messages.success(
            request,
            f"Horario {start}-{end} de la sala {room_id} bloqueado por "
            f"mantenimiento. La reserva de {quien} pasó a estado "
            "POR_MANTENIMIENTO (sin penalización).",
        )
    else:
        messages.success(
            request,
            f"Horario {start}-{end} de la sala {room_id} bloqueado por "
            "mantenimiento. No había ninguna reserva asociada a ese horario.",
        )

    return redirect("dashboard")
