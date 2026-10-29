import pytest
from django.contrib.auth.hashers import make_password
from django.urls import reverse

from reservas.gestion_salas import (
    GestionSalasError,
    create_room,
    create_room_schedule,
    remove_room_schedule,
)
from reservas.models import Horario, Rol, Sala, SalaHorario, Usuario


@pytest.mark.django_db
def test_administrador_no_puede_abrir_ni_enviar_la_gestion_de_salas(client):
    admin = Usuario.objects.create(
        codigo_usuario=900100,
        rol=Rol.objects.create(nombre_rol="Administrador"),
        email="admin-gestion@test.edu",
        nombre="Admin",
        apellido="Pruebas",
        password_hash=make_password("clave-admin"),
    )
    client.post(reverse("login"), {
        "identificador": str(admin.pk), "password": "clave-admin",
    })

    ruta = reverse("gestion_salas")
    assert client.get(ruta).status_code == 404
    for accion in ("crear_sala", "crear_horario", "retirar_horario"):
        assert client.post(ruta, {"accion": accion, "nombre_sala": "Sala nueva"}).status_code == 404

    assert Sala.objects.count() == 0
    assert Horario.objects.count() == 0
    assert SalaHorario.objects.count() == 0
    assert "Gestión de salas y horarios" not in client.get(reverse("dashboard")).content.decode()


@pytest.mark.django_db
def test_servicios_de_gestion_tambien_rechazan_las_altas_y_retiros():
    for operacion, argumentos in (
        (create_room, (900100, "Sala nueva")),
        (create_room_schedule, (900100, 1, "07:45", "09:45")),
        (remove_room_schedule, (900100, 1)),
    ):
        with pytest.raises(GestionSalasError, match="deshabilitada"):
            operacion(*argumentos)

    assert Sala.objects.count() == 0
    assert Horario.objects.count() == 0
    assert SalaHorario.objects.count() == 0
