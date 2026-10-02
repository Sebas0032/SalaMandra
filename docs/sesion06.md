# Sesión 6 — Hallazgos y requisitos del proyecto

- Proyecto: SalaMandra — Sistema de Reserva de Salas de Estudio
- Integrantes: Luciana Soza (@luci-solar34), Sebastian Cruz (@Sebas0032), Sebastian Toledo (@sebas-sst)
- Fecha: 01 de octubre de 2026
- Cliente o fuente consultada: Sergio Barrientos (Docente / Cliente)
- Flujo seleccionado: Gestión, modificación, cancelación y bloqueos de reservas de salas (PB-01 / PB-03 / PB-04)

## 1. Hallazgos de la entrevista

| ID | Pregunta | Respuesta o hallazgo | Fuente | Estado |
|---|---|---|---|---|
| ENT-01 | ¿Qué pasa si alguien intenta modificar una reserva que ya empezó? | Solo se puede modificar una reserva siempre y cuando sea al menos una hora (1 hora) antes del inicio de la reserva. Si ya comenzó o falta menos de 1 hora, no se permite la modificación. | Sergio | Confirmado |
| ENT-02 | ¿Puede un estudiante cancelar una reserva sin penalización? | Tiene penalización si cancela con menos de tres horas (3 horas) de anticipación. La sanción es escalar: 1ra vez = bloqueo por 24 horas; 2da vez = 48 horas; 3ra vez = 1 semana; 4ta vez = todo el semestre. | Sergio | Confirmado |
| ENT-03 | ¿Se puede bloquear una sala para mantenimiento aunque haya reservas? | Sí se puede. El usuario de Mantenimiento / Administración tiene el poder necesario para cancelar las reservas activas y bloquear la sala en caso de presentarse algún problema. | Sergio | Confirmado |

## 2. Alcance del flujo

- Incluye: Validación del tiempo de modificación (mínimo 1 hora antes); control de cancelaciones con penalización según bloque de 3 horas; registro y escala progresiva de sanciones a estudiantes (24h, 48h, 1 semana, todo el semestre); facultad de rol de Mantenimiento para cancelar reservas existentes y bloquear salas.
- No incluye: Pago o multas monetarias. Envíos automáticos de correos o notificaciones.

## 3. Requisitos

### [RES-RF-01 — Restricción de tiempo para modificación de reserva]

- Tipo: Funcional
- Origen: ENT-01 y encargo inicial (RES-05)
- Prioridad y razón: Alta; garantiza la previsibilidad de uso de las salas y evita cambios de último momento.
- Estado: Aprobado por el cliente
- Requisito: El sistema debe permitir modificar una reserva únicamente si la solicitud se realiza con al menos 1 hora de anticipación respecto a la hora de inicio. De lo contrario, la solicitud debe ser rechazada manteniendo la reserva original.
- Criterio de aceptación o comprobación:
  - Situación inicial: Reserva confirmada para la sala "A-101" a las 14:00.
  - Acción: Intentar cambiar el horario de la reserva a las 13:15 (a menos de 1 hora del inicio).
  - Resultado esperado: El sistema rechaza la modificación con una excepción explícita. La reserva se mantiene confirmada a las 14:00 en "A-101".

---

### [RES-RF-02 — Cancelación con sistema escalar de penalizaciones]

- Tipo: Funcional
- Origen: ENT-02
- Prioridad y razón: Alta; desincentiva la cancelación tardía y promueve la disponibilidad oportuna de salas.
- Estado: Aprobado por el cliente
- Requisito: Si un estudiante cancela una reserva con menos de 3 horas de anticipación, el sistema debe registrar una falta y aplicar un bloqueo temporal para realizar nuevas reservas según la escala: 1ª vez (24h), 2ª vez (48h), 3ª vez (1 semana) y 4ª vez (todo el semestre).
- Criterio de aceptación o comprobación:
  - Situación inicial: Estudiante "92345" con reserva a las 10:00 y 0 sanciones registradas.
  - Acción: Cancela la reserva a las 08:00 (a 2 horas del inicio).
  - Resultado esperado: La reserva se cancela, se registra la 1ª sanción en el historial del estudiante y se aplica un bloqueo automático que le impide reservar durante las siguientes 24 horas.

---

### [RES-RF-03 — Bloqueo de sala por Mantenimiento y cancelación de reservas]

- Tipo: Funcional
- Origen: ENT-03
- Prioridad y razón: Alta; es una necesidad operativa crítica para atender contingencias físicas en la infraestructura del campus.
- Estado: Aprobado por el cliente
- Requisito: El sistema debe permitir que un usuario con rol de Mantenimiento bloquee una sala por imprevistos. Si existen reservas confirmadas en esa sala, el sistema debe cancelarlas automáticamente cambiando su estado a "CANCELADA_POR_MANTENIMIENTO".
- Criterio de aceptación o comprobación:
  - Situación inicial: Sala "B-102" con reserva activa para las 15:00 del estudiante "92345".
  - Acción: Usuario con rol Mantenimiento efectúa un bloqueo por fuga de agua en "B-102".
  - Resultado esperado: La sala "B-102" pasa a estado "EN_MANTENIMIENTO" y la reserva del estudiante pasa a "CANCELADA_POR_MANTENIMIENTO" sin aplicar penalización al estudiante.

---

### [RES-RF-04 — Verificación de bloqueo de estudiante al intentar reservar]

- Tipo: Funcional
- Origen: ENT-02
- Prioridad y razón: Alta; asegura el cumplimiento efectivo de las sanciones generadas por cancelaciones tardías.
- Estado: Aprobado por el cliente
- Requisito: El sistema debe verificar si un estudiante tiene una sanción/bloqueo vigente al momento de intentar crear cualquier nueva reserva. Si el bloqueo está activo, la reserva debe ser rechazada.
- Criterio de aceptación o comprobación:
  - Situación inicial: Estudiante "92345" con sanción activa de 24 horas aplicada hace 2 horas.
  - Acción: Intenta crear una nueva reserva en cualquier sala disponible.
  - Resultado esperado: El sistema rechaza la solicitud indicando que el estudiante se encuentra bloqueado y muestra el tiempo restante de la sanción.

---

### [RES-RC-01 — Claridad en mensajes de penalización e impedimentos]

- Tipo: Calidad
- Origen: Adaptación de ejemplo de la guía
- Prioridad y razón: Media; proporciona retroalimentación transparente al usuario sobre por qué no puede realizar la operación.
- Estado: Aprobado por el cliente
- Requisito: Ante el rechazo de una operación por penalización o bloqueo de mantenimiento, el sistema debe mostrar un mensaje explicativo detallado con el motivo exacto y la duración del bloqueo.
- Criterio de aceptación o comprobación:
  - Situación inicial: Estudiante sancionado intenta realizar una reserva.
  - Acción: Ejecutar la solicitud de reserva desde el sistema.
  - Resultado esperado: El sistema genera una excepción o mensaje claro (ej. "No puede reservar: tiene una sanción activa por cancelación tardía (1ª falta) vigente hasta [Fecha/Hora]"). Un mensaje genérico como "Error" no es válido.

---

### [RES-RT-01 — Persistencia de penalizaciones y reservas en Django ORM]

- Tipo: Restricción
- Origen: Especificación técnica del proyecto semestral
- Prioridad y razón: Alta; garantiza la integridad del modelo de datos e historial de sanciones dentro de la arquitectura elegida.
- Estado: Aprobado por el cliente
- Requisito: La lógica de sanciones, historial de cancelaciones y bloqueos de mantenimiento debe implementarse en Python y persistirse mediante los modelos de Django ORM.
- Criterio de comprobación posterior:
  - Situación inicial: Modelos `Student`, `Reservation` y `Sanction` / `Maintenance` creados.
  - Acción: Ejecutar la suite de pruebas unitarias sobre los métodos del servicio de cancelaciones y mantenimiento.
  - Resultado esperado: Las transacciones y actualización de estados se reflejan correctamente en la base de datos a través del ORM de Django.

## 4. Escenarios del flujo

| Caso | Requisito relacionado | Datos y acción | Resultado esperado |
|---|---|---|---|
| Normal | RES-RF-01 | Reserva confirmada a las 16:00. Solicitud de cambio de hora enviada a las 14:30 (1.5 horas antes). | Se aprueba la modificación y se actualiza el horario de la reserva. |
| Límite | RES-RF-01 | Reserva confirmada a las 16:00. Solicitud de cambio de hora enviada a las 15:00 (exactamente 1 hora antes). | Se aprueba la modificación al cumplir la regla límite de 1 hora previa. |
| Rechazo | RES-RF-02 | Reserva confirmada a las 12:00. Cancelación enviada a las 10:30 (menos de 3 horas antes, 1ra vez). | La reserva se cancela, se registra la 1ª falta y el estudiante queda bloqueado de hacer reservas por 24 horas. |

Estos escenarios están especificados; serán integrados en la suite de pruebas automatizadas en `pytest` / Django Test Runner para la siguiente iteración.

## 5. Preguntas y decisiones pendientes

| Pregunta | AQuién consultar | Impacto mientras no se resuelva |
|---|---|---|
| ¿El período del semestre para la 4ta sanción tiene una fecha de reinicio automática al inicio del siguiente periodo académico? | Sergio (Cliente) | Afecta la lógica de expiración de las sanciones en la base de datos a largo plazo. |


## 6. Siguiente paso

- Tarea: Modelar las entidades `Sanction` y `Maintenance` en `models.py` de Django e implementar las funciones de cancelación tardía y bloqueo en `services.py`.
- Requisito relacionado: RES-RF-02 y RES-RF-03
- Responsable inicial: Sebastian Cruz (@Sebas0032)
- Issue: Issue #15 en el repositorio del proyecto en GitHub.

## 7. Participación y asistencia utilizada

- Aportes de cada integrante: 
  - Luciana Soza: Conducción de la entrevista al cliente, formulación de las preguntas sobre modificaciones y mantenimiento, y redacción de los hallazgos `ENT-01` y `ENT-03`.
  - Sebastian Cruz: Definición de los requisitos funcionales de penalizaciones escalar (`RES-RF-02`) y restricciones de tiempo (`RES-RF-01`), y configuración del Issue.
  - Sebastian Toledo: Elaboración de criterios de aceptación, diseño de escenarios del flujo y redacción de la restricción técnica `RES-RT-01`.
- Asistencia de IA, si se utilizó: ChatGPT / Gemini para estructurar las respuestas de la entrevista en la plantilla estándar de la Sesión 6 de GitHub en formato Markdown.