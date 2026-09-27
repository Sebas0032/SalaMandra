# Iteración de la Sesión 04

## Equipo y proyecto
Reserva de salas de estudio — SalaMandra

| Integrante | GitHub |
|---|---|
| Luciana Soza | @luci-solar34 |
| Sebastian Cruz | @Sebas0032 |
| Sebastian Toledo | @sebas-sst |

Cliente simulado: UPB Santa Cruz (Bolivia), sistema de reserva de salas de estudio. El docente, Sergio Barrientos, actúa como cliente.

Facilitador y controlador del tiempo: **Luciana Soza** — indica cuándo rotan los roles (quién escribe, quién revisa, quién valida) cada ~10 minutos. Los tres roles rotan entre Luciana, Sebastian Cruz y Sebastian Toledo para que todos pasen por cada responsabilidad. Nos coordinamos por Google Meet.

## Backlog ordenado

| Orden | ID | Capacidad | ¿A quién ayuda y para qué? | Duda pendiente |
|---|---|---|---|---|
| 1 | PB-01 | Validar código del solicitante y crear una reserva | Al solicitante y al operador, para verificar que el solicitante está registrado y permitir el registro de una reserva válida. | ¿La información del solicitante se autocompleta desde la base de datos o se ingresará manualmente? — (aclarada, ver abajo) |
| 2 | PB-02 | Consultar espacios disponibles | Al solicitante y al operador, para encontrar un espacio según la fecha, horario y capacidad. | ¿Existe un intervalo de tiempo entre reservas para el desalojo? — (aclarada, ver abajo) |
| 3 | PB-03 | Modificar una reserva | Al solicitante para modificar su reserva y al operador para ayudarlo. | ¿Hasta cuánto tiempo antes se permite modificar? — (aclarada, ver abajo) |
| 4 | PB-04 | Cancelar una reserva | Al estudiante para cancelar su reserva y al operador para ayudarlo. | ¿Hasta cuánto tiempo antes se permite cancelar? |
| 5 | PB-05 | Gestionar salas y horarios | Al administrador, para crear salas y establecer los horarios disponibles. | ¿Se pueden crear horarios especiales para una sala? |

**Razón de la prioridad:** elegimos PB-01 como primera capacidad a implementar porque resuelve la necesidad central del cliente: permitir que un solicitante pueda reservar una sala de estudio de forma sencilla, verificando que esté registrado. Sus reglas (validación de código, capacidad, conflicto de horario, límite de una reserva por bloque) ya fueron aclaradas con Sergio en las respuestas de cliente. Aunque la solicitante es una característica nueva de esta iteración (antes era solo "crear reserva"), la refactorización a POO con clases separadas para Student, Room y Reservation permite testear cada regla de forma independiente usando datos ficticios en memoria, sin necesidad de implementar PB-02 y PB-05 todavía.

## Objetivo y alcance

> Al finalizar, el solicitante podrá crear una reserva de una sala de estudio, previa validación de su código de estudiante y respetando la restricción de una reserva activa por horario.

**Alcance técnico:**
-  Verificación de la existencia del código de estudiante en los registros del sistema
-  Restricción de máximo una reserva por solicitante en un mismo bloque de horario
-  Validación del margen de tiempo de 15 minutos entre bloques de reserva
-  Ejecución de pruebas automatizadas con pytest

**Fuera de alcance:**
-  Interfaz de usuario (UI), base de datos persistente (SQL/NoSQL) y servidores web
-  Modificación y cancelación de reservas (PB-03, PB-04)
-  Gestión de salas y horarios (PB-05)

**Pregunta de control:** sí, se demuestra ejecutando las pruebas de PB-01, sin funcionalidades que todavía no existen.

## Aclaraciones del cliente

| Pregunta | Respuesta del cliente | Efecto sobre el comportamiento esperado |
|---|---|---|
| ¿Existe un intervalo de tiempo entre reservas para el desalojo? | Se propone un intervalo de 15 minutos. | El sistema permite iniciar una nueva reserva solo si han pasado 15 minutos desde que terminó la reserva anterior de esa sala. |
| ¿La información del solicitante se autocompleta desde la base de datos o se ingresará manualmente? | La información deberá autocompletar desde la base de datos. | Para esta iteración, simulamos la base de datos con datos ficticios en memoria; el estudiante se valida por su código. |
| ¿Cuántas salas puede reservar un alumno por horario? | Una sala. | Un alumno no puede tener dos reservas activas en el mismo bloque horario, incluso si son en salas distintas. |
| ¿Hasta cuánto tiempo antes se permite modificar? | Se permitirá modificar una reserva hasta 10 minutos después de haber sido realizada. | Queda pendiente para PB-03 (fuera del alcance de esta iteración). |
| ¿Hasta cuánto tiempo antes se permite cancelar? | Pendiente de confirmación. Se plantea inicialmente considerar un límite de una hora. | Queda pendiente para PB-04 (fuera del alcance de esta iteración). |

**Pendiente:** cómo se estructura la base de datos de estudiantes (será relevante para PB-02); penalizaciones por cancelaciones múltiples; mecanismo de login/autenticación (a acordar en una iteración posterior).

## Ejemplos de aceptación

| Caso | Estado inicial y entrada | Resultado esperado | Regla que lo justifica |
|---|---|---|---|
| **Uso normal** | **Estado:** El solicitante con código 92345 está registrado. La Sala de estudio A (capacidad 6) está libre en el bloque 10:00–12:00. **Entrada:** Código 92345, sala A-101, horario 10:00–12:00, 4 asistentes, actividad "Estudios". | El sistema valida los datos, registra la reserva y retorna estado CONFIRMADA con un ID de reserva (ej. RES-001). | Una reserva puede confirmarse cuando: (1) el código existe, (2) la sala tiene capacidad, (3) no hay conflicto de horario, (4) el estudiante no tiene otra reserva en ese bloque. |
| **Límite** | **Estado:** Existe una reserva en Sala A-101 de 07:45–09:45 (otro estudiante). **Entrada:** Estudiante 92345 solicita Sala A-101, 10:00–12:00. | Se registra exitosamente. Retorna CONFIRMADA. Las dos reservas coexisten (una no afecta a la otra). | El término a las 09:45 + intervalo de 15 min = 10:00 (inicio permitido). No hay conflicto. |
| **Rechazo: doble reserva en bloque** | **Estado:** Estudiante 92345 ya tiene una reserva en Sala B-102 para 10:00–12:00. **Entrada:** Intenta reservar Sala A-101 para el mismo bloque 10:00–12:00, código 92345. | El sistema rechaza con mensaje: "El estudiante 92345 ya tiene una reserva en ese bloque" (StudentAlreadyBookedError). La reserva anterior se conserva sin cambios. | Un alumno puede reservar una sola sala por bloque de horario, aunque sean salas distintas. |

## Plan y seguimiento

**Definition of Done:**
- [ ] Los 3 ejemplos de aceptación tienen pruebas ejecutables que pasan.
- [ ] Las pruebas incluyen casos de validación adicionales (sala no existe, capacidad insuficiente).
- [ ] Las pruebas anteriores (si las hay) continúan pasando.
- [ ] El código fue revisado por otro integrante en un PR.
- [ ] La contribución está integrada en `main` y fue comprobada allí.
- [ ] El README permite ejecutar las pruebas (`python -m pytest -v`).
- [ ] El equipo puede demostrar el resultado y explicar sus límites.

**Interfaz mínima (finalizada):**

```text
# Clases de dominio
class Student:
    def __init__(self, code: str, first_name: str, last_name: str)
    def full_name() -> str

class Room:
    def __init__(self, room_id: str, name: str, capacity: int)
    def has_capacity(attendees: int) -> bool

class Reservation:
    def __init__(self, reservation_id: int, room_id: str, student_code: str, 
                 start: str, end: str, activity_detail: str, status: str = "CONFIRMADA")

# Funciones de negocio
def has_time_conflict(reservations: list, room_id: str, start: str, end: str, buffer_minutes: int = 15) -> bool

def has_active_reservation_in_block(reservations: list, student_code: str, start: str, end: str) -> bool

def create_reservation(rooms: dict, reservations: list, room_id: str, student_code: str, 
                       start: str, end: str, attendees: int, activity_detail: str) -> Reservation

# Excepciones personalizadas
class RoomNotFoundError(Exception)
class CapacityExceededError(Exception)
class StudentAlreadyBookedError(Exception)
class TimeConflictError(Exception)

# Estructura de datos
rooms:        diccionario {room_id -> Room}
reservations: lista de Reservation (todas activas en esta iteración)
```

Cada prueba arma su propio conjunto de salas y reservas ficticias en memoria.

| Tarea | Personas que colaboran | Estado | Evidencia o ubicación |
|---|---|---|---|
| T1. Definir y documentar los ejemplos de aceptación de PB-01 | Todo el equipo |  Terminado | docs/sesion04.md |
| T2. Implementar clases POO (Student, Room, Reservation) | Todo el equipo |  Terminado | proyecto/estudiante.py, proyecto/sala.py, proyecto/reserva.py |
| T3. Definir excepciones personalizadas | Todo el equipo |  Terminado | proyecto/excepciones.py |
| T4. Crear las pruebas (pytest) del caso normal, límite y rechazo | Todo el equipo (rotando) |  Terminado | tests/test_reglas.py |
| T5. Implementar funciones helper (has_time_conflict, has_active_reservation_in_block) | Todo el equipo (rotando) |  Terminado | proyecto/reglas.py |
| T6. Implementar create_reservation | Todo el equipo (rotando) |  Terminado | proyecto/reglas.py |
| T7. Ejecutar pytest, pasar todas las pruebas, revisar y refactorizar | Todo el equipo (rotando) |  Terminado | tests/test_reglas.py / proyecto/reglas.py |
| T8. Integrar en main, verificar que pytest pasa, preparar demostración | Todo el equipo | Por hacer | GitHub / main |

Sesión de programación en grupo: _(25/09/2026 — 27/09/2026)_, por Google Meet. Horario: 10:00–12:00 → Break 1 hora → 14:00–18:00 (total 5 horas de trabajo). La rotación real (quién escribe, quién revisa, quién valida) y el punto de inspección se registran durante la sesión.

## Verificación e integración
**Ejecutar todas las pruebas**

python -m pytest -v

**Ejecutar solo las pruebas de un caso**

python -m pytest tests/test_reglas.py::TestCrearReservaUsoCasoNormal -v

**Ver resultado detallado con output**

python -m pytest -vv --tb=short

**Correr con cobertura (opcional, requiere pip install pytest-cov)**

python -m pytest --cov=proyecto tests/

### Pruebas ejecutadas

Se ejecutó la suite de pruebas automatizadas con pytest para verificar las reglas implementadas para la creación de reservas.

### Resultado

*8 tests passed.*

Las pruebas verificaron:

- Creación correcta de una reserva válida.
- Validación de estudiantes registrados.
- Rechazo de estudiantes no registrados.
- Aplicación del intervalo mínimo de 15 minutos entre reservas.
- Rechazo de reservas simultáneas del mismo estudiante.
- Rechazo cuando la sala no existe.
- Rechazo cuando la cantidad de asistentes supera la capacidad de la sala.

### Pull Request
    
[PR#8](https://github.com/Sebas0032/SalaMandra/pull/8)

### Commit demostrado

fix: validate student before creating reservation

El cambio valida el código del estudiante antes de procesar la creación de la reserva y evita que una solicitud con un estudiante no registrado modifique la lista de reservas.

## Retroalimentación
Pendiente — petición o defecto identificado en la revisión y cambio correspondiente en el backlog, segun lo recomendado del cliente (Sergio).

## Retrospectiva
**Mantener:** Rotar roles (Driver, Navigator, Validator) cada 10 o 15 minutos por Google Meet. Esto permitió que todos los integrantes comprendieran la arquitectura POO y mantuvieran el código libre de errores al momento de hacer commits.
**Cambiar:** La falta de definición clara e inicial de las firmas de los métodos y parámetros en los test casos, lo que causó fallos de incompatibilidad temporal (TypeError por orden de parámetros) durante las pruebas integradas.
**Experimentar:** Crear un archivo de datos de prueba compartidos (salas y estudiantes base) para no tener que volver a escribir Room("A-101", ...) en cada archivo de test, lo impulsa Sebastian Soto y comprobaremos si el archivo de pruebas es más corto, claro y rápido de escribir en la siguiente sesión.


## Planificación y adaptación
**¿Qué decisión necesitaba planificación antes de programar?**
La estructura y modelado de datos en POO (separar Student, Room y Reservation) y definir cómo se representaría el tiempo y los bloques de reserva. Planificar esto con anticipación evitó rehacer la lógica de validación de conflictos.

**¿Qué decisión pudieron mejorar gracias a una prueba o a la revisión del cliente?**
La regla de negocio sobre reservas simultáneas por un mismo estudiante. Las pruebas      automatizadas permitieron detectar que el sistema permitía reservas dobles en el mismo bloque si eran en salas distintas, lo cual se corrigió agregando la función has_active_reservation_in_block.

**¿En qué contexto de su proyecto sería útil fijar más detalles por anticipado? ¿Qué costo tendría hacerlo si las reglas todavía cambian?**
Sería útil definir con precisión la política de cancelaciones y modificaciones (PB-03 y PB-04) y los estados permitidos en el ciclo de vida de una reserva.
El costo de hacerlo por anticipado: Si fijamos reglas rígidas de tiempo (ej. "solo se cancela con 1 hora de anticipación") sin validarlo con el cliente, tendríamos que reescribir gran parte de la lógica de validación, modificar la estructura de las excepciones y rehacer todas las pruebas unitarias cuando el cliente decida cambiar los límites de tiempo.

