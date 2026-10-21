"""Registro y autenticación de cuentas de SalaMandra."""

from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction

from reservas.models import Rol, Usuario, UsuarioRol


ROL_ADMINISTRADOR = "Administrador"


def usuario_tiene_rol(codigo_usuario, nombre_rol):
    return UsuarioRol.objects.filter(
        usuario_id=codigo_usuario, rol__nombre_rol=nombre_rol
    ).exists()


def authenticate_user(identificador, password):
    """Autentica una cuenta activa únicamente por código y contraseña."""
    codigo = _parse_codigo_usuario(identificador)
    if codigo is None:
        return None

    usuario = Usuario.objects.filter(pk=codigo).first()
    if usuario is None or not usuario.estado_usuario or not usuario.password_hash:
        return None
    if not check_password(password, usuario.password_hash):
        return None
    return usuario if _usuario_tiene_rol_permitido(usuario) else None


def _parse_codigo_usuario(identificador):
    if not (
        identificador.isascii()
        and identificador.isdigit()
        and len(identificador) <= 19
    ):
        return None
    codigo = int(identificador)
    if not 0 < codigo <= 9223372036854775807:
        return None
    return codigo


def _usuario_tiene_rol_permitido(usuario):
    return UsuarioRol.objects.filter(
        usuario=usuario,
        rol__nombre_rol__in=["Administrador", "Solicitante", "Estudiante", "Operador"],
    ).exists()


class RegistrationError(Exception):
    """Error esperado al intentar registrar una cuenta."""


@transaction.atomic
def register_student_account(codigo_usuario, email, password):
    """Activa una fila precargada de usuarios si código y correo coinciden."""
    usuario = Usuario.objects.filter(codigo_usuario=codigo_usuario).first()
    if usuario is None:
        raise RegistrationError("El código de estudiante no está registrado.")

    if not usuario.estado_usuario:
        raise RegistrationError("Este usuario está inactivo y no puede registrarse.")

    correo_registrado = usuario.email.strip().casefold()
    correo_ingresado = email.strip().casefold()
    if correo_registrado != correo_ingresado:
        raise RegistrationError("El correo no corresponde al código ingresado.")

    # Una contraseña vacía indica que la fila de la lista local aún no tiene cuenta.
    # El UPDATE condicional evita activar dos registros concurrentes para el mismo código.
    filas_actualizadas = Usuario.objects.filter(
        codigo_usuario=codigo_usuario,
        password_hash="",
    ).update(password_hash=make_password(password))
    if filas_actualizadas == 0:
        raise RegistrationError("Este código ya tiene una cuenta registrada.")

    usuario.refresh_from_db(fields=["password_hash"])
    rol_solicitante, _ = Rol.objects.get_or_create(nombre_rol="Solicitante")
    UsuarioRol.objects.get_or_create(usuario=usuario, rol=rol_solicitante)
    return usuario
