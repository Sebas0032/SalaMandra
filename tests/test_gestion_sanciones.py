from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from django.utils import timezone

from cuentas.services import authenticate_user
from reservas import gestion_sanciones
from reservas import services
from reservas.models import Rol, Sancion, TipoSancion, Usuario


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def hasher_rapido(settings):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture
def usuarios_sanciones(client):
    rol_admin = Rol.objects.get_or_create(nombre_rol="Administrador")[0]
    rol_solicitante = Rol.objects.get_or_create(nombre_rol="Solicitante")[0]
    admin = Usuario.objects.create(
        rol=rol_admin,
        pk=900001,
        email="admin@salamandra.test",
        nombre="Admin",
        apellido="Prueba",
        password_hash=make_password("admin123"),
    )
    estudiante = Usuario.objects.create(
        rol=rol_solicitante,
        pk=101145,
        email="sebastiancruz1@upb.edu",
        nombre="Sebastian",
        apellido="Cruz",
        password_hash=make_password("clave-segura"),
    )
    client.post(
        reverse("login"),
        {"identificador": str(admin.pk), "password": "admin123"},
    )
    return admin, estudiante


def test_aplica_sancion_manual_con_motivo_y_duracion(usuarios_sanciones):
    admin, estudiante = usuarios_sanciones
    ahora = timezone.make_aware(datetime(2026, 10, 27, 9))
    with patch(
        "reservas.gestion_sanciones.timezone.localtime",
        return_value=ahora,
    ):
        sancion = gestion_sanciones.apply_manual_sanction(
            admin.pk,
            estudiante.pk,
            "1_semana",
            "Uso indebido de la sala",
        )

    assert sancion.usuario == estudiante
    assert sancion.origen == Sancion.Origen.MANUAL
    assert sancion.aplicada_por == admin
    assert sancion.motivo == "Uso indebido de la sala"
    assert sancion.tipo_sancion.duracion == 168
    assert sancion.tipo_sancion_id == TipoSancion.ID_1_SEMANA
    assert TipoSancion.objects.count() == 4
    assert sancion.fecha_inicio == ahora
    assert sancion.fecha_fin == ahora + timedelta(hours=168)


def test_listado_muestra_solo_la_sancion_vigente(usuarios_sanciones):
    admin, estudiante = usuarios_sanciones
    ahora = timezone.make_aware(datetime(2026, 10, 27, 9))
    tipo = TipoSancion.objects.get(pk=TipoSancion.ID_24_HORAS)
    Sancion.objects.create(
        origen=Sancion.Origen.MANUAL, aplicada_por=admin,
        usuario=estudiante,
        tipo_sancion=tipo,
        motivo="Sanción vencida",
        fecha_inicio=ahora - timedelta(days=2),
        fecha_fin=ahora - timedelta(days=1),
    )
    vigente = Sancion.objects.create(
        origen=Sancion.Origen.MANUAL, aplicada_por=admin,
        usuario=estudiante,
        tipo_sancion=tipo,
        motivo="Sanción vigente",
        fecha_inicio=ahora - timedelta(hours=1),
        fecha_fin=ahora + timedelta(hours=23),
    )

    filas = gestion_sanciones.get_solicitantes(
        filtro="sancionados", ahora=ahora
    )
    assert len(filas) == 1
    assert filas[0]["usuario"] == estudiante
    assert filas[0]["sancion"] == vigente


def test_reinicio_manual_conserva_historial_y_registra_retiro(usuarios_sanciones):
    admin, estudiante = usuarios_sanciones
    ahora = timezone.localtime()
    tipo = TipoSancion.objects.get(pk=TipoSancion.ID_24_HORAS)
    for dias in (1, 30):
        Sancion.objects.create(
            origen=Sancion.Origen.MANUAL, aplicada_por=admin,
            usuario=estudiante,
            tipo_sancion=tipo,
            motivo="Historial",
            fecha_inicio=ahora - timedelta(days=dias),
            fecha_fin=ahora + timedelta(days=1),
        )

    cantidad = gestion_sanciones.clear_all_sanctions(admin.pk)
    assert cantidad == 2
    assert Sancion.objects.count() == 2
    assert Sancion.objects.filter(
        retirada_por=admin, fecha_retiro__isnull=False
    ).count() == 2
    assert not gestion_sanciones.sanciones_vigentes(timezone.localtime()).exists()
    assert TipoSancion.objects.filter(pk=tipo.pk).exists()


def test_desactivar_cuenta_cierra_sesion_e_impide_login(
    client, usuarios_sanciones
):
    admin, estudiante = usuarios_sanciones
    client.get(reverse("logout"))
    client.post(
        reverse("login"),
        {"identificador": str(estudiante.pk), "password": "clave-segura"},
    )
    assert client.session["codigo_usuario"] == estudiante.pk

    gestion_sanciones.set_student_active_status(
        admin.pk, estudiante.pk, activo=False
    )
    response = client.get(reverse("student_panel"))
    assert response.url == reverse("login")
    assert "codigo_usuario" not in client.session
    assert authenticate_user(str(estudiante.pk), "clave-segura") is None

    gestion_sanciones.set_student_active_status(
        admin.pk, estudiante.pk, activo=True
    )
    assert authenticate_user(str(estudiante.pk), "clave-segura") == estudiante


def test_pantalla_administrativa_procesa_sancion_estado_y_reinicio(
    client, usuarios_sanciones
):
    _, estudiante = usuarios_sanciones
    response = client.get(reverse("sanctions_admin"))
    assert response.status_code == 200
    assert "Sebastian Cruz" in response.content.decode()

    response = client.post(
        reverse("apply_sanction"),
        {
            "codigo_solicitante": estudiante.pk,
            "duracion": "24_horas",
            "motivo": "Conducta indebida",
        },
    )
    assert response.url == reverse("sanctions_admin")
    assert Sancion.objects.filter(usuario=estudiante).exists()

    client.post(
        reverse("change_student_status", args=[estudiante.pk]),
        {"nuevo_estado": "0"},
    )
    estudiante.refresh_from_db()
    assert not estudiante.estado_usuario

    client.post(reverse("clear_sanctions"))
    assert Sancion.objects.count() == 1
    assert Sancion.objects.get().fecha_retiro is not None


def test_solicitante_no_puede_administrar_sanciones(
    client, usuarios_sanciones
):
    _, estudiante = usuarios_sanciones
    client.get(reverse("logout"))
    client.post(
        reverse("login"),
        {"identificador": str(estudiante.pk), "password": "clave-segura"},
    )
    assert client.get(reverse("sanctions_admin")).status_code == 403
    assert client.post(reverse("clear_sanctions")).status_code == 403


@pytest.mark.parametrize("cambio", [datetime(2027, 1, 1), datetime(2027, 7, 1)])
def test_semestre_libera_y_reinicia_sin_borrar(usuarios_sanciones, cambio):
    _, estudiante = usuarios_sanciones
    frontera = timezone.make_aware(cambio)
    anterior = frontera - timedelta(seconds=1)
    sancion = services._registrar_sancion_por_cancelacion(estudiante.pk, anterior)
    assert gestion_sanciones.contar_faltas(estudiante, anterior) == 1
    assert gestion_sanciones.sanciones_vigentes(anterior).exists()
    assert gestion_sanciones.contar_faltas(estudiante, frontera) == 0
    assert not gestion_sanciones.sanciones_vigentes(frontera).exists()
    services._validar_sin_sancion(estudiante, frontera)
    sancion.refresh_from_db()
    assert sancion.fecha_retiro is None
    assert sancion.retirada_por is None
    assert sancion.fecha_fin == anterior + timedelta(hours=24)
    nueva = services._registrar_sancion_por_cancelacion(estudiante.pk, frontera)
    assert nueva.tipo_sancion.duracion == 24
    assert gestion_sanciones.contar_faltas(estudiante, frontera) == 1
    assert Sancion.objects.count() == 2


def test_reinicio_manual_corta_contador_sin_perder_faltas_vencidas(usuarios_sanciones):
    admin, estudiante = usuarios_sanciones
    ahora = timezone.make_aware(datetime(2026, 10, 28, 12))
    vencida = services._registrar_sancion_por_cancelacion(
        estudiante.pk, ahora - timedelta(days=10)
    )
    vigente = services._registrar_sancion_por_cancelacion(
        estudiante.pk, ahora - timedelta(hours=1)
    )
    fin = vigente.fecha_fin
    with patch("reservas.gestion_sanciones.timezone.localtime", return_value=ahora):
        assert gestion_sanciones.clear_all_sanctions(admin.pk) == 1
    assert gestion_sanciones.contar_faltas(estudiante, ahora) == 0
    services._validar_sin_sancion(estudiante, ahora)
    vencida.refresh_from_db()
    vigente.refresh_from_db()
    assert vencida.fecha_retiro is None
    assert vigente.fecha_fin == fin
    assert vigente.fecha_retiro == ahora
    assert vigente.retirada_por == admin
    nueva = services._registrar_sancion_por_cancelacion(
        estudiante.pk, ahora + timedelta(seconds=1)
    )
    assert nueva.tipo_sancion.duracion == 24
    assert Sancion.objects.count() == 3


def test_retiro_individual_preserva_contador_y_rechaza_repeticion(usuarios_sanciones):
    admin, estudiante = usuarios_sanciones
    ahora = timezone.localtime()
    sancion = services._registrar_sancion_por_cancelacion(estudiante.pk, ahora)
    with pytest.raises(gestion_sanciones.GestionSancionesError):
        gestion_sanciones.withdraw_sanction(estudiante.pk, sancion.pk)
    gestion_sanciones.withdraw_sanction(admin.pk, sancion.pk)
    sancion.refresh_from_db()
    assert sancion.retirada_por == admin
    assert sancion.fecha_retiro is not None
    assert gestion_sanciones.contar_faltas(estudiante, timezone.localtime()) == 1
    assert not gestion_sanciones.get_solicitantes(filtro="sancionados")
    with pytest.raises(gestion_sanciones.GestionSancionesError):
        gestion_sanciones.withdraw_sanction(admin.pk, sancion.pk)


def test_retiro_exige_post_y_conserva_registro(client, usuarios_sanciones):
    admin, estudiante = usuarios_sanciones
    sancion = gestion_sanciones.apply_manual_sanction(
        admin.pk, estudiante.pk, "24_horas", "Prueba"
    )
    url = reverse("withdraw_sanction", args=[sancion.pk])
    assert client.get(url).status_code == 405
    assert client.post(url).status_code == 302
    sancion.refresh_from_db()
    assert sancion.retirada_por == admin
    assert Sancion.objects.count() == 1
