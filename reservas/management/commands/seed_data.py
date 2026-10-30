"""
Comando: python manage.py seed_data

Carga en la base de datos los datos mínimos para probar el caso de uso RES-CU-02:

    - roles: Administrador, Operante y Solicitante
    - usuarios: Administrador, Operante y 16 estudiantes sin cuenta activada
    - tipo_sancion: catálogo de RES-RF-02
    - salas, horarios y sus combinaciones (sala_horario)
    - 2 reservas CONFIRMADA de ejemplo

Es seguro ejecutarlo varias veces: no duplica lo que ya existe.
Usa --reset para borrar TODOS los datos de estas tablas y empezar de cero.
"""

from datetime import time, timedelta

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from reservas.models import (
    Auditoria,
    Bloqueo,
    Desbloqueo,
    Horario,
    Notificacion,
    ReinicioSanciones,
    Reserva,
    Rol,
    Sala,
    SalaHorario,
    Sancion,
    TipoSancion,
    Usuario,
)

ADMIN_EMAIL = "admin@salamandra.upb.edu"
ADMIN_PASSWORD = "admin123"
ADMIN_CODIGO_USUARIO = 900001
OPERANTE_EMAIL = "operante@salamandra.upb.edu"
OPERANTE_PASSWORD = "Operante_2026!"
OPERANTE_CODIGO_USUARIO = 900003
ALUMNOS = (
    (95445, "95445@salamandra.test", "Santiago", "Arauz"),
    (94186, "94186@salamandra.test", "Sofía", "Arduz"),
    (94102, "94102@salamandra.test", "Gonzalo", "Cardenas"),
    (101145, "101145@salamandra.test", "Sebastian", "Cruz"),
    (87097, "87097@salamandra.test", "Ismael", "Diaz"),
    (86289, "86289@salamandra.test", "Marcos", "Dominguez"),
    (89352, "89352@salamandra.test", "Andrew", "Laura"),
    (94635, "94635@salamandra.test", "Katrina", "Leigue"),
    (91870, "91870@salamandra.test", "Alejandro", "Parraga"),
    (95429, "95429@salamandra.test", "Luciana", "Soledad"),
    (94008, "94008@salamandra.test", "Sebastian", "Soto"),
    (94302, "94302@salamandra.test", "Peter", "Teran"),
    (94046, "94046@salamandra.test", "Andrea", "Trujillo"),
    (95187, "95187@salamandra.test", "Raul", "Vaca"),
    (95503, "95503@salamandra.test", "Hugo", "Zuñiga"),
    (95343, "95343@salamandra.test", "Lucas", "Leibovich"),
)


class Command(BaseCommand):
    help = "Carga datos de ejemplo en la base de datos (salas, horarios, reservas y el Administrador)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Borra todos los datos de las tablas de SalaMandra antes de cargar.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            # Orden: primero las tablas que dependen de otras.
            for modelo in (
                Notificacion, Auditoria, Desbloqueo, Bloqueo,
                ReinicioSanciones, Reserva, SalaHorario, Sancion,
                Sala, Horario, TipoSancion, Usuario, Rol,
            ):
                modelo.objects.all().delete()
            self.stdout.write(self.style.WARNING("Tablas de SalaMandra vaciadas."))

        # --- roles ---------------------------------------------------------
        rol_admin, _ = Rol.objects.get_or_create(nombre_rol="Administrador")
        rol_operante, _ = Rol.objects.get_or_create(nombre_rol="Operante")
        rol_estudiante, _ = Rol.objects.get_or_create(nombre_rol="Solicitante")

        # --- usuarios ------------------------------------------------------
        admin, creado = Usuario.objects.get_or_create(
            email=ADMIN_EMAIL,
            defaults={
                "codigo_usuario": ADMIN_CODIGO_USUARIO,
                "rol": rol_admin,
                "nombre": "Admin",
                "apellido": "SalaMandra",
                "estado_usuario": True,
                "password_hash": make_password(ADMIN_PASSWORD),
            },
        )
        if creado:
            self.stdout.write(self.style.SUCCESS(
                f"Administrador creado -> {ADMIN_EMAIL} / {ADMIN_PASSWORD}"
            ))

        operante, operante_creado = Usuario.objects.get_or_create(
            codigo_usuario=OPERANTE_CODIGO_USUARIO,
            defaults={
                "rol": rol_operante,
                "email": OPERANTE_EMAIL,
                "nombre": "Operante",
                "apellido": "SalaMandra",
                "estado_usuario": True,
                "password_hash": make_password(OPERANTE_PASSWORD),
            },
        )
        if operante_creado:
            self.stdout.write(self.style.SUCCESS(
                f"Operante creado -> código {operante.pk} / {OPERANTE_PASSWORD}"
            ))

        for codigo, email, nombre, apellido in ALUMNOS:
            Usuario.objects.get_or_create(
                codigo_usuario=codigo,
                defaults={
                    "rol": rol_estudiante,
                    "email": email,
                    "nombre": nombre,
                    "apellido": apellido,
                    "estado_usuario": True,
                    "password_hash": "",
                },
            )
        estudiante = Usuario.objects.get(codigo_usuario=95429)

        # --- tipo_sancion (catálogo de RES-RF-02) ----------------------------
        for tipo_id, nombre, horas in TipoSancion.CATALOGO:
            TipoSancion.objects.update_or_create(
                pk=tipo_id,
                defaults={"nombre_sancion": nombre, "duracion": horas},
            )

        # --- salas ---------------------------------------------------------
        salas = {
            letra: Sala.objects.get_or_create(
                nombre_sala=f"Sala de estudio {letra}",
                defaults={"estado_sala": True},
            )[0]
            for letra in "ABCDEF"
        }

        # --- horarios ------------------------------------------------------
        intervalos = (
            (time(7, 45), time(9, 45)),
            (time(10, 0), time(12, 0)),
            (time(12, 15), time(14, 15)),
            (time(14, 30), time(16, 30)),
            (time(16, 45), time(18, 45)),
            (time(19, 0), time(21, 0)),
        )
        horarios = [
            Horario.objects.get_or_create(hora_inicio=inicio, hora_fin=fin)[0]
            for inicio, fin in intervalos
        ]

        # --- sala_horario --------------------------------------------------
        sala_horarios = {
            (letra, horario.hora_inicio): SalaHorario.objects.get_or_create(
                sala=sala, horario=horario
            )[0]
            for letra, sala in salas.items()
            for horario in horarios
        }

        # --- reservas (solo si todavía no hay ninguna) ------------------------
        if not Reserva.objects.exists():
            manana = timezone.localdate() + timedelta(days=1)
            reserva_manana = Reserva.objects.create(
                usuario=estudiante, sala_horario=sala_horarios[("A", time(10, 0))],
                tipo_actividad="Estudios", fecha=manana,
            )
            reserva_tarde = Reserva.objects.create(
                usuario=estudiante, sala_horario=sala_horarios[("B", time(14, 30))],
                tipo_actividad="Trabajo en grupo", fecha=manana,
            )
            Auditoria.objects.bulk_create([
                Auditoria(reserva=reserva, actor=admin, accion=Auditoria.Accion.CREAR)
                for reserva in (reserva_manana, reserva_tarde)
            ])
            self.stdout.write(self.style.SUCCESS("Reservas de ejemplo creadas."))

        self.stdout.write(self.style.SUCCESS(
            "Listo. Ahora ejecuten: python manage.py runserver"
        ))
