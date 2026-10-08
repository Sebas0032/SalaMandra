"""
Comando: python manage.py seed_data

Crea en MongoDB los datos mínimos para probar el caso de uso RES-CU-02,
siguiendo el modelo de datos del equipo (usuarios, roles, usuarios_roles,
tipo_sancion, salas, horarios, sala_horario, reservas, bloqueos).

`tipo_sancion` se carga como catálogo (coincide con la escala de
RES-RF-02 de docs/sesion-06-requisitos.md), pero `sanciones` se deja
vacía: la lógica para aplicar sanciones todavía no está implementada,
queda para una iteración futura.

Es seguro ejecutarlo varias veces: si ya existen datos, no los duplica.
Usa --reset para borrar todo y empezar de cero.
"""

from datetime import datetime, timezone

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand

from reservas.mongo import get_db

COLECCIONES = [
    "usuarios",
    "roles",
    "usuarios_roles",
    "tipo_sancion",
    "sanciones",
    "horarios",
    "salas",
    "sala_horario",
    "reservas",
    "bloqueos",
    "counters",
]


class Command(BaseCommand):
    help = "Carga datos de ejemplo en MongoDB según el modelo de datos del equipo."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Borra las colecciones de SalaMandra antes de volver a cargarlas.",
        )

    def handle(self, *args, **options):
        db = get_db()

        if options["reset"]:
            for nombre in COLECCIONES:
                db[nombre].delete_many({})
            self.stdout.write(self.style.WARNING("Colecciones de SalaMandra limpiadas."))

        # --- roles ---------------------------------------------------------
        if db.roles.count_documents({}) == 0:
            db.roles.insert_many(
                [
                    {"id_rol": 1, "nombre_rol": "Administrador"},
                    {"id_rol": 2, "nombre_rol": "Estudiante"},
                ]
            )
            self.stdout.write(self.style.SUCCESS("Roles creados: Administrador, Estudiante"))
        else:
            self.stdout.write("Ya existían roles, no se modificaron.")

        # --- usuarios --------------------------------------------------------
        # NOTA: `password_hash` no está en el diagrama original del equipo;
        # se agregó solo porque el login necesita guardar la contraseña de
        # alguna forma. Es la única diferencia respecto al esquema enviado.
        if db.usuarios.count_documents({}) == 0:
            db.usuarios.insert_many(
                [
                    {
                        "codigo_usuario": 1,
                        "email": "admin@salamandra.upb.edu",
                        "nombre": "Admin",
                        "apellido": "SalaMandra",
                        "estado_usuario": True,
                        "fecha_creacion": datetime.now(timezone.utc),
                        "password_hash": make_password("admin123"),
                    },
                    {
                        "codigo_usuario": 2,
                        "email": "luciana.perez@upb.edu",
                        "nombre": "Luciana",
                        "apellido": "Perez",
                        "estado_usuario": True,
                        "fecha_creacion": datetime.now(timezone.utc),
                    },
                ]
            )
            self.stdout.write(
                self.style.SUCCESS(
                    "Usuarios creados -> Administrador: "
                    "admin@salamandra.upb.edu / admin123"
                )
            )
        else:
            self.stdout.write("Ya existían usuarios, no se modificaron.")

        # --- usuarios_roles ----------------------------------------------------
        if db.usuarios_roles.count_documents({}) == 0:
            db.usuarios_roles.insert_many(
                [
                    {"id_usuario_roles": 1, "id_rol": 1, "codigo_usuario": 1},
                    {"id_usuario_roles": 2, "id_rol": 2, "codigo_usuario": 2},
                ]
            )
            self.stdout.write(self.style.SUCCESS("Rol Administrador asignado al usuario admin."))
        else:
            self.stdout.write("Ya existían asignaciones de rol, no se modificaron.")

        # --- tipo_sancion (catálogo; RES-RF-02, sin lógica implementada aún) ----
        if db.tipo_sancion.count_documents({}) == 0:
            db.tipo_sancion.insert_many(
                [
                    {"id_tipo_sancion": 1, "nombre_sancion": "Cancelación tardía (1ra vez)", "duracion": 24},
                    {"id_tipo_sancion": 2, "nombre_sancion": "Cancelación tardía (2da vez)", "duracion": 48},
                    {"id_tipo_sancion": 3, "nombre_sancion": "Cancelación tardía (3ra vez)", "duracion": 168},
                    {"id_tipo_sancion": 4, "nombre_sancion": "Cancelación tardía (4ta vez)", "duracion": 9999},
                ]
            )
            self.stdout.write(
                self.style.SUCCESS(
                    "Catálogo tipo_sancion creado (sin lógica implementada todavía)."
                )
            )
        else:
            self.stdout.write("Ya existía el catálogo tipo_sancion, no se modificó.")

        # --- salas -----------------------------------------------------------
        if db.salas.count_documents({}) == 0:
            db.salas.insert_many(
                [
                    {"id_salas": 1, "nombre_sala": "Sala de estudio A", "estado_sala": True},
                    {"id_salas": 2, "nombre_sala": "Sala de estudio B", "estado_sala": True},
                ]
            )
            self.stdout.write(self.style.SUCCESS("Salas creadas: Sala de estudio A, Sala de estudio B"))
        else:
            self.stdout.write("Ya existían salas, no se modificaron.")

        # --- horarios ----------------------------------------------------------
        if db.horarios.count_documents({}) == 0:
            db.horarios.insert_many(
                [
                    {"id_horario": 1, "hora_inicio": "10:00", "hora_fin": "12:00"},
                    {"id_horario": 2, "hora_inicio": "15:00", "hora_fin": "17:00"},
                ]
            )
            self.stdout.write(self.style.SUCCESS("Horarios creados: 10:00-12:00, 15:00-17:00"))
        else:
            self.stdout.write("Ya existían horarios, no se modificaron.")

        # --- sala_horario ----------------------------------------------------
        if db.sala_horario.count_documents({}) == 0:
            db.sala_horario.insert_many(
                [
                    {
                        "id_sala_horario": 1,
                        "id_sala": 1,
                        "id_horario": 1,
                        "estado_sala_horario": "DISPONIBLE",
                    },
                    {
                        "id_sala_horario": 2,
                        "id_sala": 2,
                        "id_horario": 2,
                        "estado_sala_horario": "DISPONIBLE",
                    },
                ]
            )
            self.stdout.write(
                self.style.SUCCESS(
                    "Combinaciones sala+horario creadas: "
                    "Sala A/10:00-12:00 (id 1), Sala B/15:00-17:00 (id 2)."
                )
            )
        else:
            self.stdout.write("Ya existían combinaciones sala_horario, no se modificaron.")

        # --- reservas ----------------------------------------------------------
        if db.reservas.count_documents({}) == 0:
            db.reservas.insert_many(
                [
                    {
                        "id_reserva": 1,
                        "codigo_usuario": 2,
                        "id_sala_horario": 1,
                        "tipo_actividad": "Estudios",
                        "fecha": "2026-10-08",
                        "estado_reserva": "CONFIRMADA",
                    },
                    {
                        "id_reserva": 2,
                        "codigo_usuario": 2,
                        "id_sala_horario": 2,
                        "tipo_actividad": "Trabajo en grupo",
                        "fecha": "2026-10-08",
                        "estado_reserva": "CONFIRMADA",
                    },
                ]
            )
            self.stdout.write(
                self.style.SUCCESS("Reservas de ejemplo creadas (estudiante Luciana Perez).")
            )
        else:
            self.stdout.write("Ya existían reservas, no se modificaron.")

        self.stdout.write(self.style.SUCCESS("Listo. Ahora ejecuten: python manage.py runserver"))
