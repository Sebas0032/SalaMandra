import pytest
from django.contrib.auth.hashers import check_password, make_password
from django.urls import resolve, reverse

from cuentas import views
from reservas.models import Rol, Usuario


pytestmark = [pytest.mark.django_db, pytest.mark.e2e]


def test_login_y_logout_del_administrador(client):
    admin = Usuario.objects.create(
        rol=Rol.objects.get_or_create(nombre_rol="Administrador")[0],
        codigo_usuario=900001, email="admin@salamandra.test",
        nombre="Admin", apellido="Prueba", password_hash=make_password("admin123"),
    )

    assert reverse("login") == "/login/"
    assert resolve("/login/").func is views.login_view
    assert resolve("/logout/").func is views.logout_view
    assert client.get(reverse("login")).status_code == 200
    response = client.post(reverse("login"), {
        "identificador": str(admin.pk), "password": "admin123",
    })
    assert response.url == reverse("dashboard")
    assert client.session["codigo_usuario"] == admin.pk
    assert client.get(reverse("dashboard")).status_code == 200

    response = client.get(reverse("logout"))
    assert response.url == reverse("login")
    assert "codigo_usuario" not in client.session
    assert client.get(reverse("dashboard")).url == reverse("login")


def test_login_solicitante_y_acceso_restringido(client):
    usuario = Usuario.objects.create(
        rol=Rol.objects.get_or_create(nombre_rol="Solicitante")[0],
        codigo_usuario=95429, email="95429@salamandra.test",
        nombre="Luciana", apellido="Soledad", password_hash=make_password("clave"),
    )
    for datos in (
        {"identificador": usuario.email, "password": "clave"},
        {"email": usuario.email, "password": "clave"},
    ):
        assert client.post(reverse("login"), datos).status_code == 200
        assert "codigo_usuario" not in client.session
    response = client.post(reverse("login"), {
        "identificador": str(usuario.pk), "password": "clave",
    })
    assert response.url == reverse("dashboard")
    assert client.session["codigo_usuario"] == usuario.pk
    assert client.get(reverse("dashboard")).url == reverse("student_panel")
    assert client.get(reverse("student_panel")).status_code == 200
    assert client.post(reverse("block_room")).status_code == 403


def test_registro_conserva_validacion_y_no_reemplaza_contrasena(client):
    usuario = Usuario.objects.create(
        rol=Rol.objects.get_or_create(nombre_rol="Solicitante")[0],
        codigo_usuario=95429, email="95429@salamandra.test",
        nombre="Luciana", apellido="Soledad",
    )
    assert reverse("registro") == "/cuentas/registro/"
    assert client.get(reverse("registro")).status_code == 200
    datos = {
        "codigo_usuario": usuario.pk,
        "email": "otro@salamandra.test",
        "password": "SalaMandra_2026!",
        "password_confirmation": "SalaMandra_2026!",
    }
    assert client.post(reverse("registro"), datos).status_code == 400
    usuario.refresh_from_db()
    assert usuario.password_hash == ""

    datos["email"] = usuario.email
    assert client.post(reverse("registro"), datos).url == reverse("login")
    usuario.refresh_from_db()
    assert check_password("SalaMandra_2026!", usuario.password_hash)
    assert usuario.rol.nombre_rol == "Solicitante"

    datos["password"] = "OtraClave_2026!"
    datos["password_confirmation"] = "OtraClave_2026!"
    assert client.post(reverse("registro"), datos).status_code == 400
    usuario.refresh_from_db()
    assert check_password("SalaMandra_2026!", usuario.password_hash)
