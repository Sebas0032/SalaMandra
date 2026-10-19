from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.db import OperationalError, ProgrammingError
from django.shortcuts import redirect, render

from .services import RegistrationError, authenticate_user, register_student_account, parse_codigo_usuario

# ----------------------------------------------------------------------------------------
# Para el registro de cuentas de Nuevos Usuarios (Solicitantes)
def register_view(request):
    error = None
    valores = {"codigo_usuario": "", "email": ""}

    if request.method == "POST":
        codigo_usuario = request.POST.get("codigo_usuario", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        valores = {"codigo_usuario": codigo_usuario, "email": email}

        try:
            codigo = parse_codigo_usuario(codigo_usuario)
            if codigo is None:
                raise RegistrationError("Ingresa un código de estudiante válido.")

            if not email or len(email) > 255:
                raise RegistrationError("Ingresa un correo válido.")
            try:
                EmailValidator()(email)
            except ValidationError as exc:
                raise RegistrationError("Ingresa un correo válido.") from exc
            if not password.strip():
                raise RegistrationError("La contraseña no puede estar vacía.")
            # tomando en cuenta esto mas adelante para nosotros hacer nuestra contra 1234
            # if len(password) <= 8:
            #     raise RegistrationError("La contraseña debe tener al menos 8 caracteres.")
            if len(password) > 128:
                raise RegistrationError("La contraseña no puede superar 128 caracteres.")

            usuario = register_student_account(
                codigo_usuario=codigo,
                email=email,
                password=password,
            )
        except RegistrationError as exc:
            error = str(exc)
        else:
            messages.success(
                request,f"Cuenta de Solicitante creada correctamente para {usuario.nombre}.",)
            return redirect("login")

    return render(
        request,
        "cuentas/registro.html",
        {"error": error, **valores},
        status=400 if error else 200,
    )
# ----------------------------------------------------------------------------------------
# Para el login de Administradores y Solicitantes
def login_view(request):
    if request.session.get("codigo_usuario"):
        return redirect("dashboard")

    if request.method == "POST":
        identificador = request.POST.get("identificador", "").strip()
        password = request.POST.get("password", "")

        try:
            usuario = authenticate_user(identificador, password)
        except (OperationalError, ProgrammingError) as exc:
            return render(
                request, "reservas/db_error.html", {"error": str(exc)}, status=503
            )

        if usuario:
            request.session.flush()
            request.session["codigo_usuario"] = usuario.codigo_usuario
            request.session["nombre_completo"] = str(usuario)
            messages.success(request, f"Bienvenido/a, {usuario.nombre}.")
            return redirect("dashboard")

        messages.error(
            request,
            "Código o contraseña incorrectos, o cuenta no habilitada.",
        )

    return render(request, "cuentas/login.html")

# ----------------------------------------------------------------------------------------
# Para el logout de Administradores / Solicitantes
def logout_view(request):
    request.session.flush()
    messages.success(request, "Sesión cerrada correctamente.")
    return redirect("login")
