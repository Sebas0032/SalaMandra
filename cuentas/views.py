from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.db import OperationalError, ProgrammingError
from django.shortcuts import redirect, render

from .services import RegistrationError, authenticate_user, register_student_account

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
            if not codigo_usuario.isdecimal() or int(codigo_usuario) <= 0:
                raise RegistrationError("Ingresa un código de estudiante válido.")
            if int(codigo_usuario) > 9223372036854775807:
                raise RegistrationError("El código de estudiante no es válido.")
            if not email or len(email) > 255:
                raise RegistrationError("Ingresa un correo válido.")
            try:
                EmailValidator()(email)
            except ValidationError as exc:
                raise RegistrationError("Ingresa un correo válido.") from exc
            if len(password) > 128:
                raise RegistrationError("La contraseña no puede superar 128 caracteres.")
            try:
                validate_password(password)
            except ValidationError as exc:
                raise RegistrationError(" ".join(exc.messages)) from exc

            usuario = register_student_account(
                codigo_usuario=int(codigo_usuario),
                email=email,
                password=password,
            )
        except RegistrationError as exc:
            error = str(exc)
        else:
            messages.success(
                request,
                f"Cuenta de Solicitante creada correctamente para {usuario.nombre}.",
            )
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
