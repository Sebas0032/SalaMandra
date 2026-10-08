"""
Comando: python manage.py seed_data

Crea en MongoDB los datos mínimos para poder probar el caso de uso
RES-CU-02 (bloqueo de horario por mantenimiento):

    - 2 salas (rooms)
    - 2 reservas CONFIRMADA (reservations), una por cada sala
    - 1 usuario Administrador (admins): admin / admin123

Es seguro ejecutarlo varias veces: si ya existen datos, no los duplica.
Usa --reset para borrar todo y empezar de cero.
"""

from datetime import datetime, timezone

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand

from reservas.mongo import get_db


class Command(BaseCommand):
    help = "Carga datos de ejemplo en MongoDB (salas, reservas y el usuario Administrador)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Borra las colecciones de SalaMandra antes de volver a cargarlas.",
        )

    def handle(self, *args, **options):
        db = get_db()

        if options["reset"]:
            db.rooms.delete_many({})
            db.reservations.delete_many({})
            db.bloqueos.delete_many({})
            db.admins.delete_many({})
            self.stdout.write(self.style.WARNING("Colecciones de SalaMandra limpiadas."))

        if db.rooms.count_documents({}) == 0:
            db.rooms.insert_many(
                [
                    {"room_id": "A-101", "name": "Sala de estudio A", "capacity": 6},
                    {"room_id": "B-102", "name": "Sala de estudio B", "capacity": 4},
                ]
            )
            self.stdout.write(self.style.SUCCESS("Salas creadas: A-101, B-102"))
        else:
            self.stdout.write("Ya existían salas, no se modificaron.")

        if db.reservations.count_documents({}) == 0:
            db.reservations.insert_many(
                [
                    {
                        "room_id": "A-101",
                        "student_code": "92345",
                        "student_name": "Luciana Perez",
                        "start": "10:00",
                        "end": "12:00",
                        "activity_detail": "Estudios",
                        "status": "CONFIRMADA",
                    },
                    {
                        "room_id": "B-102",
                        "student_code": "92345",
                        "student_name": "Luciana Perez",
                        "start": "15:00",
                        "end": "17:00",
                        "activity_detail": "Trabajo en grupo",
                        "status": "CONFIRMADA",
                    },
                ]
            )
            self.stdout.write(self.style.SUCCESS(
                "Reservas de ejemplo creadas (incluye la del ejemplo de "
                "docs/sesion-06-requisitos.md: sala B-102, 15:00, estudiante 92345)."
            ))
        else:
            self.stdout.write("Ya existían reservas, no se modificaron.")

        if db.admins.count_documents({"username": "admin"}) == 0:
            db.admins.insert_one(
                {
                    "username": "admin",
                    "password_hash": make_password("admin123"),
                    "created_at": datetime.now(timezone.utc),
                }
            )
            self.stdout.write(self.style.SUCCESS(
                "Usuario Administrador creado -> usuario: admin / contraseña: admin123"
            ))
        else:
            self.stdout.write("El usuario Administrador ya existía, no se modificó.")

        self.stdout.write(self.style.SUCCESS(
            "Listo. Ahora ejecuten: python manage.py runserver"
        ))
