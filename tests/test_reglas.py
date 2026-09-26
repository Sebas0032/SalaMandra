"""Pruebas de las reglas de negocio.

Cada prueba debe:
- Tener un nombre que empiece con test_ y describa el comportamiento
  (ej. test_rechaza_codigo_con_formato_invalido).
- Preparar el estado/entradas, invocar la función real y comparar
  el resultado (y el estado posterior, si aplica) con lo acordado.
- Estar basada en uno de los ejemplos de docs/sesion04.md, no en un
  valor inventado sin regla que lo respalde.

from proyecto.reglas import ...  # importen aquí lo que vayan probando
"""
from proyecto import Room, Student, Reservation, create_reservation


def test_crear_reserva_caso_normal():
    # Armar datos
    room = Room("A-101", "Sala de estudio A", 6)
    rooms = {"A-101": room}
    reservations = []

    # Llamar la función
    result = create_reservation(
        rooms, reservations, "A-101", "92345", "10:00", "12:00", 4,
        "Comer Hamburguesas")

    # Verificar
    assert result.status == "CONFIRMADA"
    assert result.student_code == "92345"
    assert result.activity_detail == "Estudios"

    def test_estudiante_con_nombre_completo():
        student = Student("92345", "Juan", "Pérez")
        assert student.full_name() == "Juan Pérez"
        assert student.code == "92345"