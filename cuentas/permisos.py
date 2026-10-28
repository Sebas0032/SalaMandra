"""Acceso a las vistas según la cuenta y su rol actual."""
from functools import wraps
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from reservas.models import Rol, Usuario
from .services import usuario_tiene_rol


def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        usuario = Usuario.objects.filter(
            pk=request.session.get("codigo_usuario"), estado_usuario=True,
            rol__nombre_rol__in=Rol.Nombre.values,
        ).first()
        if usuario is None or not usuario.password_hash:
            request.session.flush()
            messages.error(request, "Debes iniciar sesión para continuar.")
            return redirect("login")
        request.usuario = usuario
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_login_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not usuario_tiene_rol(request.usuario.pk, "Administrador"):
            return HttpResponseForbidden("Solo un Administrador puede realizar esta operación.")
        return view_func(request, *args, **kwargs)
    return wrapper


def operante_login_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not usuario_tiene_rol(request.usuario.pk, Rol.Nombre.OPERANTE):
            return HttpResponseForbidden("Solo un Operante puede realizar esta operación.")
        return view_func(request, *args, **kwargs)
    return wrapper
