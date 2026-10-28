"""
Comando: python manage.py seed_data

Carga en la base de datos los datos mínimos para probar el caso de uso RES-CU-02:

    - roles: Administrador, Operante y Solicitante
    - usuarios: un Administrador (con login) y una estudiante (sin login)
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
    Horario,
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
ESTUDIANTE_CODIGO_USUARIO = 900002


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
                Auditoria, Bloqueo, Reserva, SalaHorario, Sancion,
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

        estudiante, _ = Usuario.objects.get_or_create(
            email="luciana.perez@upb.edu",
            defaults={
                "codigo_usuario": ESTUDIANTE_CODIGO_USUARIO,
                "rol": rol_estudiante,
                "nombre": "Luciana",
                "apellido": "Perez",
                "estado_usuario": True,
            },
        )

        # --- tipo_sancion (catálogo de RES-RF-02) ----------------------------
        for nombre, horas in (
            ("Cancelación tardía (1ra vez)", 24),
            ("Cancelación tardía (2da vez)", 48),
            ("Cancelación tardía (3ra vez)", 168),
            ("Cancelación tardía (4ta vez, todo el semestre)", 9999),
        ):
            TipoSancion.objects.get_or_create(
                nombre_sancion=nombre, defaults={"duracion": horas}
            )

        # --- salas ---------------------------------------------------------
        sala_a, _ = Sala.objects.get_or_create(
            nombre_sala="Sala de estudio A", defaults={"estado_sala": True}
        )
        sala_b, _ = Sala.objects.get_or_create(
            nombre_sala="Sala de estudio B", defaults={"estado_sala": True}
        )

        # --- horarios ------------------------------------------------------
        h_manana, _ = Horario.objects.get_or_create(
            hora_inicio=time(10, 0), hora_fin=time(12, 0)
        )
        h_tarde, _ = Horario.objects.get_or_create(
            hora_inicio=time(15, 0), hora_fin=time(17, 0)
        )

        # --- sala_horario --------------------------------------------------
        sh_a_manana, _ = SalaHorario.objects.get_or_create(sala=sala_a, horario=h_manana)
        sh_b_tarde, _ = SalaHorario.objects.get_or_create(sala=sala_b, horario=h_tarde)

        # --- reservas (solo si todavía no hay ninguna) ------------------------
        if not Reserva.objects.exists():
            manana = timezone.localdate() + timedelta(days=1)
            reserva_manana = Reserva.objects.create(
                usuario=estudiante, sala_horario=sh_a_manana,
                tipo_actividad="Estudios", fecha=manana,
            )
            reserva_tarde = Reserva.objects.create(
                usuario=estudiante, sala_horario=sh_b_tarde,
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
