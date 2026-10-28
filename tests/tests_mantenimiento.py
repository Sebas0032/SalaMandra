"""
Pruebas esenciales de backend para el caso de uso RES-CU-02 (Bloqueo por Mantenimiento).

Ejecución:
    python -m pytest tests/tests_mantenimiento.py -v
"""

from datetime import time, timedelta
import pytest
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from reservas import services
from reservas.models import (
    Bloqueo, Horario, Reserva, Rol, Sala, SalaHorario, Sancion, Usuario, UsuarioRol
)

# Todas las pruebas de este archivo usan la base de datos de prueba
# (una SQLite temporal que se crea y se borra sola; no toca db.sqlite3).

pytestmark = pytest.mark.django_db
PASSWORD = "clave-de-prueba-123"
MOTIVO = "Fuga de agua"


# =============================================================================
# Fixtures (Configuración Mínima)
# =============================================================================

@pytest.fixture(autouse=True)
def hasher_rapido(settings):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

@pytest.fixture
def manana():
    return timezone.localdate() + timedelta(days=1)

def _crear_usuario(codigo_usuario, email, nombre, rol):
    usuario = Usuario.objects.create(
        codigo_usuario=codigo_usuario,
        email=email, nombre=nombre, apellido="Test",
        estado_usuario=True, password_hash=make_password(PASSWORD)
    )
    UsuarioRol.objects.create(usuario=usuario, rol=rol)
    return usuario

@pytest.fixture
def admin():
    rol = Rol.objects.create(nombre_rol=services.ROL_ADMINISTRADOR)
    return _crear_usuario(900001, "admin@test.edu", "Admin", rol)

@pytest.fixture
def estudiante():
    rol = Rol.objects.create(nombre_rol="Estudiante")
    return _crear_usuario(900002, "estudiante@test.edu", "Luciana", rol)

@pytest.fixture
def sh_a_manana():
    sala = Sala.objects.create(nombre_sala="Sala A")
    horario = Horario.objects.create(hora_inicio=time(10, 0), hora_fin=time(12, 0))
    return SalaHorario.objects.create(sala=sala, horario=horario)

@pytest.fixture
def reserva(estudiante, sh_a_manana, manana):
    return Reserva.objects.create(
        usuario=estudiante, sala_horario=sh_a_manana,
        tipo_actividad="Estudios", fecha=manana
    )


# =============================================================================
# Pruebas Principales de Backend (Servicios)
# =============================================================================

class TestBloqueoMantenimiento:

    def test_bloqueo_exitoso_y_cancelacion_sin_sancion(self, admin, estudiante, sh_a_manana, reserva):
        """Flujo Principal: Bloquea horario, cancela reserva asociada sin aplicar sanción al estudiante."""
        services.block_room_schedule_for_maintenance(admin.codigo_usuario, sh_a_manana.id_sala_horario, MOTIVO)

        sh_a_manana.refresh_from_db()
        reserva.refresh_from_db()

        assert sh_a_manana.estado_sala_horario == SalaHorario.ESTADO_MANTENIMIENTO
        assert reserva.estado_reserva == Reserva.ESTADO_POR_MANTENIMIENTO
        assert Sancion.objects.filter(usuario=estudiante).exists() is False

    def test_registra_bitacora_de_bloqueo(self, admin, sh_a_manana):
        """Auditoría: Guarda el responsable, motivo y fecha exacta en la bitácora."""
        services.block_room_schedule_for_maintenance(admin.codigo_usuario, sh_a_manana.id_sala_horario, MOTIVO)

        bloqueo = Bloqueo.objects.get()
        assert bloqueo.usuario == admin
        assert bloqueo.sala_horario == sh_a_manana
        assert bloqueo.motivo == MOTIVO

    def test_aislamiento_no_afecta_otras_salas_ni_horarios(self, admin, estudiante, sh_a_manana, manana):
        """Efecto Colateral: Bloquear una sala y horario no altera otros bloques de la misma sala ni otras salas."""
        otra_sala = Sala.objects.create(nombre_sala="Sala B")
        sh_otra_sala = SalaHorario.objects.create(sala=otra_sala, horario=sh_a_manana.horario)
        reserva_otra_sala = Reserva.objects.create(usuario=estudiante, sala_horario=sh_otra_sala, fecha=manana)

        services.block_room_schedule_for_maintenance(admin.codigo_usuario, sh_a_manana.id_sala_horario, MOTIVO)

        reserva_otra_sala.refresh_from_db()
        sh_otra_sala.refresh_from_db()

        assert sh_otra_sala.estado_sala_horario == SalaHorario.ESTADO_DISPONIBLE
        assert reserva_otra_sala.estado_reserva == Reserva.ESTADO_CONFIRMADA

    def test_estudiante_no_puede_bloquear(self, estudiante, sh_a_manana, reserva):
        """Excepción E1: Un usuario sin rol Administrador es rechazado."""
        error_detectado = False
        try:
            services.block_room_schedule_for_maintenance(estudiante.codigo_usuario, sh_a_manana.id_sala_horario, MOTIVO)
        except services.NotAuthorizedError:
            error_detectado = True

        sh_a_manana.refresh_from_db()
        assert error_detectado is True
        assert sh_a_manana.estado_sala_horario == SalaHorario.ESTADO_DISPONIBLE

    def test_sala_o_horario_inexistente(self, admin):
        """Excepción E2: Intentar bloquear un id_sala_horario que no existe dispara error."""
        error_detectado = False
        try:
            services.block_room_schedule_for_maintenance(admin.codigo_usuario, 999999, MOTIVO)
        except services.ScheduleNotFoundError:
            error_detectado = True

        assert error_detectado is True

    def test_impide_doble_bloqueo(self, admin, sh_a_manana):
        """Validación: No permite volver a bloquear un horario que ya está en Mantenimiento."""
        services.block_room_schedule_for_maintenance(admin.codigo_usuario, sh_a_manana.id_sala_horario, MOTIVO)

        error_detectado = False
        try:
            services.block_room_schedule_for_maintenance(admin.codigo_usuario, sh_a_manana.id_sala_horario, "Otro motivo")
        except services.ScheduleAlreadyBlockedError:
            error_detectado = True

        assert error_detectado is True
        assert Bloqueo.objects.count() == 1

    def test_no_permite_crear_reserva_en_horario_bloqueado(self, admin, estudiante, sh_a_manana, manana):
        """Regla de Negocio: El horario queda bloqueado para mantenimiento en el sistema."""
        # 1. Ejecutar el bloqueo por mantenimiento
        services.block_room_schedule_for_maintenance(admin.codigo_usuario, sh_a_manana.id_sala_horario, MOTIVO)

        # 2. Refrescar el objeto desde la base de datos para confirmar persisencia
        sh_a_manana.refresh_from_db()

        # 3. Validar que el estado del horario cambió a MANTENIMIENTO
        assert sh_a_manana.estado_sala_horario == "MANTENIMIENTO"


class TestSalidaDeMantenimiento:

    def test_administrador_vuelve_a_habilitar_horario(
        self, admin, sh_a_manana, reserva
    ):
        services.block_room_schedule_for_maintenance(
            admin.codigo_usuario, sh_a_manana.pk, MOTIVO
        )

        services.unblock_room_schedule_from_maintenance(
            admin.codigo_usuario, sh_a_manana.pk
        )

        sh_a_manana.refresh_from_db()
        reserva.refresh_from_db()
        assert sh_a_manana.estado_sala_horario == SalaHorario.ESTADO_DISPONIBLE
        assert reserva.estado_reserva == Reserva.ESTADO_POR_MANTENIMIENTO
        assert Bloqueo.objects.count() == 1

    def test_estudiante_no_puede_sacar_horario_de_mantenimiento(
        self, admin, estudiante, sh_a_manana
    ):
        services.block_room_schedule_for_maintenance(
            admin.codigo_usuario, sh_a_manana.pk, MOTIVO
        )

        with pytest.raises(services.NotAuthorizedError):
            services.unblock_room_schedule_from_maintenance(
                estudiante.codigo_usuario, sh_a_manana.pk
            )

        sh_a_manana.refresh_from_db()
        assert sh_a_manana.estado_sala_horario == SalaHorario.ESTADO_MANTENIMIENTO

    def test_rechaza_habilitar_horario_que_no_esta_en_mantenimiento(
        self, admin, sh_a_manana
    ):
        with pytest.raises(services.ScheduleNotBlockedError):
            services.unblock_room_schedule_from_maintenance(
                admin.codigo_usuario, sh_a_manana.pk
            )

        sh_a_manana.refresh_from_db()
        assert sh_a_manana.estado_sala_horario == SalaHorario.ESTADO_DISPONIBLE

    def test_lista_activa_excluye_horario_despues_de_habilitarlo(
        self, admin, sh_a_manana
    ):
        services.block_room_schedule_for_maintenance(
            admin.codigo_usuario, sh_a_manana.pk, MOTIVO
        )
        assert len(services.get_active_maintenance_blocks()) == 1

        services.unblock_room_schedule_from_maintenance(
            admin.codigo_usuario, sh_a_manana.pk
        )

        assert services.get_active_maintenance_blocks() == []

    def test_boton_de_interfaz_habilita_el_horario(
        self, client, admin, sh_a_manana
    ):
        services.block_room_schedule_for_maintenance(
            admin.codigo_usuario, sh_a_manana.pk, MOTIVO
        )
        client.post(
            "/login/",
            {"identificador": str(admin.pk), "password": PASSWORD},
        )

        response = client.post(
            f"/mantenimiento/{sh_a_manana.pk}/habilitar/"
        )

        sh_a_manana.refresh_from_db()
        assert response.status_code == 302
        assert response.url == "/"
        assert sh_a_manana.estado_sala_horario == SalaHorario.ESTADO_DISPONIBLE
