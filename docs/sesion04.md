# Iteración de la Sesión 04

## Equipo y proyecto
Reserva de salas de estudio — SalaMandra

| Integrante | GitHub |
|---|---|
| Luciana Soza | @luci-solar34 |
| Sebastian Cruz | @Sebas0032 |
| Sebastian Toledo | @sebas-sst |

Cliente simulado: UPB Santa Cruz (Bolivia), sistema de reserva de salas de estudio. El docente, Sergio Barrientos, actúa como cliente.

Facilita y controla el tiempo: _(completar — indiquen si esta función también rota entre los tres, o si la asumirá una persona fija)_. Trabajamos con los tres roles rotando entre Luciana, Sebastian Cruz y Sebastian Toledo: quien escribe, quien revisa la lógica y quien valida o ejecuta las pruebas — los tres cubrimos los tres roles durante la sesión. Nos coordinamos por Google Meet en sesiones de 2 a 3 horas por día.

## Backlog ordenado

| Orden | ID | Capacidad | ¿A quién ayuda y para qué? | Duda pendiente |
|---|---|---|---|---|
| 1 | PB-01 | Consultar espacios disponibles | Al solicitante y al operador, para encontrar un espacio según la fecha, horario y capacidad. | ¿Existe un intervalo de tiempo entre reservas para el desalojo? — (aclarada, ver abajo) |
| 2 | PB-02 | Validar código de solicitante para permitir una reserva | Al solicitante, para verificar que está registrado antes de reservar. | ¿Qué hace válido un código de estudiante (formato, o existencia en un padrón)? |
| 3 | PB-03 | Crear una reserva | Al solicitante, para reservar directamente una sala. Al operador, para ayudar a registrar una reserva. | ¿Cuántas salas puede reservar un alumno por horario? — (aclarada, ver abajo) |
| 4 | PB-04 | Modificar una reserva | Al solicitante para modificar su reserva y al operador para ayudarlo. | ¿Hasta cuánto tiempo antes se permite modificar? — (aclarada, ver abajo) |
| 5 | PB-05 | Cancelar una reserva | Al estudiante para cancelar su reserva y al operador para ayudarlo. | ¿Hasta cuánto tiempo antes se permite cancelar? |

**Razón de la prioridad (borrador — decidan y ajústenlo con sus propias palabras; el Orden de la tabla y la capacidad elegida deben coincidir, ver nota):** se eligió trabajar PB-03 en esta iteración porque es la operación central del encargo de Sergio (registrar una reserva sin cruces de horario); sus reglas de capacidad, conflicto de horario y "una sala por bloque" ya fueron aclaradas con el cliente, y es alcanzable en una sesión de 2-3 horas simulando PB-01 y PB-02 con datos ficticios en memoria en vez de implementarlos todavía.

**Nota:** la tabla de arriba ordena PB-01 como prioridad 1, pero esta iteración implementa PB-03 (orden 3). Ajusten el Orden de la tabla para que PB-03 quede como 1, o dejen el orden así y expliquen aquí por qué decidieron adelantar PB-03 sobre PB-01 y PB-02.

## Objetivo y alcance

> Al finalizar, el solicitante podrá crear una reserva de una sala de estudio para un bloque horario, siempre que la sala tenga capacidad suficiente para los asistentes, no exista conflicto de horario con otra reserva de esa sala (respetando el intervalo de 15 minutos de desalojo) y el estudiante no tenga ya otra reserva activa en ese mismo bloque.

**Nota:** el objetivo original mencionaba también "código de estudiante válido" y "límite de reservas por hora", pero ninguno de los tres ejemplos de aceptación prueba esas dos reglas. Este objetivo quedó recortado a lo que sí está cubierto por los ejemplos (PB-03); "validar código" (PB-02) y el límite de reservas siguen en el backlog para una iteración posterior. Si prefieren mantenerlas en el alcance de esta entrega, hay que agregar un cuarto ejemplo que las pruebe antes de programar.

**Pregunta de control:** sí, se demuestra ejecutando las pruebas de PB-03, sin funcionalidades que todavía no existen.

**Alcance:**
- Se implementa PB-03 (crear una reserva), aplicando las reglas de capacidad, conflicto de horario (con el intervalo de 15 minutos) y una reserva por estudiante por bloque.
- El solicitante y la sala se asumen ya registrados: los datos de estudiantes y salas son fixtures en memoria que arma cada prueba, simulando PB-01 y PB-02 para esta iteración.
- Fuera de alcance: validar el formato o la existencia real del código de estudiante, modificar o cancelar reservas, penalizaciones por cancelación, base de datos, interfaz.
- El resto del backlog queda pendiente y se actualizará después de la revisión.

## Aclaraciones del cliente

| Pregunta | Respuesta del cliente | Efecto sobre el comportamiento esperado |
|---|---|---|
| ¿Existe un intervalo de tiempo entre reservas para el desalojo? | Se propone un intervalo de 15 minutos. | Especificará si el sistema permite iniciar una nueva reserva inmediatamente después de finalizar otra o si debe existir un intervalo entre ambas. |
| ¿La información del solicitante se autocompleta desde la base de datos o lo pondrá manualmente? | La información deberá autocompletar desde la base de datos. | Identificará cómo se obtienen los datos del solicitante al realizar una reserva y qué información debe proporcionar el usuario. |
| ¿Cuántas salas puede reservar un alumno por horario? | Una sala. | Establecerá si una nueva reserva del mismo estudiante debe permitirse o rechazarse. |
| ¿Hasta cuánto tiempo antes se permite modificar? | Se permitirá modificar una reserva hasta 10 minutos después de haber sido realizada. | Determinará cuándo el sistema permitirá o rechazará una modificación. |
| ¿Hasta cuánto tiempo antes se permite cancelar? | Pendiente de confirmación. Se plantea inicialmente considerar un límite de una hora y evaluar posibles penalizaciones en casos de múltiples cancelaciones o de no utilización de las aulas. | Determinará cuándo el sistema permitirá o rechazará una cancelación. |

**Pendiente:** qué hace válido un código de estudiante (formato o existencia en un padrón); límite de reservas por hora mencionado en el objetivo original; penalizaciones por cancelaciones múltiples; mecanismo de login (a acordar en una iteración posterior).

## Ejemplos de aceptación

| Caso | Estado inicial y entrada | Resultado esperado | Regla que lo justifica |
|---|---|---|---|
| Uso normal | Estado inicial: el solicitante con código 92345 está registrado. La Sala de estudio A (capacidad 6) está libre en el bloque de 10:00 a 12:00. Entrada: el estudiante ingresa código 92345, sala Sala de estudio A, horario 10:00 a 12:00 y 4 asistentes. | El sistema valida los datos, registra la reserva y retorna un estado CONFIRMADA con un ID de reserva. | Una reserva puede confirmarse cuando el solicitante está registrado, la sala cumple las condiciones de disponibilidad en ese bloque y los asistentes no superan la capacidad. |
| Límite | Estado inicial: existe una reserva confirmada en la Sala de estudio A para el turno previo de 07:45 a 09:45. Entrada: el estudiante 92345 solicita reservar la misma Sala de estudio A para el turno inmediato siguiente de 10:00 a 12:00. | Se procesa la solicitud exitosamente y retorna estado CONFIRMADA para el turno de 10:00 a 12:00. | El término de un turno (09:45) y el inicio del siguiente (10:00) respetan la separación de 15 minutos entre bloques, por lo que el bloque de 10:00 a 12:00 se considera libre sin conflicto de horario. |
| Rechazo o situación excepcional prevista | Estado inicial: el estudiante con código 92345 ya tiene una reserva activa en otra sala (ej. Sala B) para el bloque de 10:00 a 12:00. Entrada: intenta realizar una segunda reserva para la Sala de estudio A en el mismo bloque de 10:00 a 12:00 ingresando el código 92345. | El sistema rechaza la nueva reserva, conserva la reserva existente e informa que el alumno ya cuenta con un espacio reservado en ese horario. | Un alumno puede reservar una sola sala por bloque de horario. |

## Plan y seguimiento

**Definition of Done:**
- [ ] Los ejemplos acordados tienen pruebas ejecutables que pasan.
- [ ] Las pruebas anteriores del proyecto continúan pasando.
- [ ] El código fue revisado por otro integrante.
- [ ] La contribución está integrada en `main` y fue comprobada allí.
- [ ] El README permite ejecutar las pruebas.
- [ ] El equipo puede demostrar el resultado y explicar sus límites.

**Interfaz mínima (propuesta — confírmenla y ajústenla en equipo antes de programar):**

```text
Student(code)
Room(room_id, name, capacity)
Reservation(room_id, student_code, start, end, status)

has_capacity(room, attendees) -> bool
has_time_conflict(reservations, room_id, start, end, buffer_minutes) -> bool
has_active_reservation_in_block(reservations, student_code, start, end) -> bool
create_reservation(rooms, reservations, room_id, student_code, start, end, attendees) -> Reservation

rooms:        diccionario room_id -> Room
reservations: lista de Reservation (todas activas en esta iteración)
errores:      RoomNotAvailableError, CapacityExceededError, StudentAlreadyBookedError
```

Cada prueba arma su propio conjunto de salas y reservas.

| Tarea | Personas que colaboran | Estado | Evidencia o ubicación |
|---|---|---|---|
| T1. Definir y documentar los ejemplos de aceptación de PB-03 | Todo el equipo | Terminado | docs/sesion04.md |
| T2. Definir la interfaz mínima y preparar las estructuras de estudiantes, salas y reservas | Todo el equipo | Por hacer | tests/test_reglas.py |
| T3. Crear las pruebas e implementación del caso normal | Todo el equipo (rotando) | Por hacer | tests/test_reglas.py |
| T4. Implementar las funciones necesarias para crear y validar una reserva | Todo el equipo (rotando) | Por hacer | proyecto/reglas.py |
| T5. Ejecutar las pruebas, revisar y refactorizar el código | Todo el equipo (rotando) | Por hacer | tests/test_reglas.py / proyecto/reglas.py |
| T6. Integrar, ejecutar la suite completa y preparar la demostración | Todo el equipo | Por hacer | README.md / GitHub / main |

Sesión de programación en grupo: _(completar — fecha y hora exacta de inicio)_, por Google Meet, bloque de 2 a 3 horas. La rotación real y el punto de inspección se registran durante la sesión.

## Verificación e integración
Pendiente — resultado real de `python -m pytest -q`, enlace del PR y commit demostrado en `main`.

## Retroalimentación
Pendiente — petición o defecto identificado en la revisión y cambio correspondiente en el backlog.

## Retrospectiva
Pendiente — mantener, cambiar y experimentar.

## Planificación y adaptación
Pendiente — respuestas breves sobre las decisiones tomadas y su contexto.
