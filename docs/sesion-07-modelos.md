# Sesión 7 — Historias, casos de uso y modelos

- Proyecto: SalaMandra — Reserva de Salas de Estudio
- Integrantes: Luciana Soza (@luci-solar34), Sebastian Cruz (@Sebas0032), Sebastian Toledo (@sebas-sst)
- Fecha: 02 de octubre de 2026
- Requisitos de origen: [Sesión 6](sesion-06-requisitos.md)
- Flujo seleccionado: Bloqueo de sala por Mantenimiento y cancelación automática de reservas
- IDs seleccionados y estado de aprobación: RES-RF-03 (Confirmado)

---

## 1. Historia RES-HU-02

Como Adminitrador, quiero bloquear una sala cuando hay una falla o imprevisto, de modo que el sistema cancele automáticamente todas las reservas sin penalizar a los estudiantes.

- Requisitos relacionados: RES-RF-03

---

## 2. Caso de uso RES-CU-02 — Bloquear una sala por Mantenimiento

- **Objetivo:** permitir que un usuario Administrador bloquee una sala cuando hay un imprevisto, cancelando automáticamente las reservas que estaban confirmadas sin penalizar a los estudiantes.
- **Actor principal:** usuario con rol de Administrador.
- **Disparador:** el usuario Administrador detecta un problema en una sala (fuga, daño, etc.) y la bloquea.
- **Precondiciones:** 
  - La sala existe en el sistema.
  - El usuario tiene rol de Administrador (autorizado para bloquear salas).
- **Poscondición de éxito:** la sala pasa a estado EN_MANTENIMIENTO, la reserva confirmada se cambian POR_MANTENIMIENTO, ningún estudiante recibe penalización, y se registra el motivo del bloqueo.
- **Garantía ante rechazo:** la sala mantiene su estado anterior, no se cancela ninguna reserva y se informa al usuario Administrador por qué el bloqueo no fue posible.

### Flujo principal

1. El usuario Administrador bloquea una sala identificándola (por ID o nombre).
2. El sistema valida que la sala exista y que el usuario tenga permisos de Administrador.
3. El sistema verifica que la sala no esté ya bloqueada.
4. El sistema busca la reserva confirmada (independientemente de el bloque de horario).
5. Para la reserva encontrada, el sistema cambia su estado a POR_MANTENIMIENTO sin registrar penalización.
6. El sistema cambia el estado de la sala a EN_MANTENIMIENTO.
7. El sistema registra el motivo del bloqueo (ej: "No hay electricidad") y la fecha/hora.
8. El sistema confirma que el bloqueo fue exitoso y lista la reserva cancelada.

### E1 — Rechazo: usuario sin permisos de Administrador, paso 2

- **Ocurre en el paso:** 2 (validación de permisos).
- **Condición:** el usuario que solicita bloquear no tiene rol de Administrador.
- **Respuesta del sistema:** 
  - Rechaza la solicitud.
  - Informa: "No tienes permisos para bloquear salas. Contacta al administrador."
- **Estado final y datos que se conservan:** 
  - La sala sigue con su estado anterior (DISPONIBLE o EN_USO).
  - Ninguna reserva se modifica.
- **El caso termina sin hacer cambios.**

### E2 — Rechazo: sala no existe, paso 2

- **Ocurre en el paso:** 2 (validación de existencia).
- **Condición:** el ID o nombre de la sala no corresponde a ninguna sala en el sistema.
- **Respuesta del sistema:** 
  - Rechaza la solicitud.
  - Informa: "La sala [ID] no existe en el sistema."
- **Estado final y datos que se conservan:** 
  - No hay cambios en el sistema.
- **El caso termina sin hacer cambios.**

---

## 3. Modelo RES-MOD-02 — Bloqueo de sala y cancelación automática

- **Tipo elegido:** Diagrama de actividad simplificado
- **Pregunta que responde:** ¿Qué ocurre cuando se solicita bloquear una sala? ¿Quién puede hacerlo? ¿Qué cambia en la sala y sus reservas?
- **Alcance y aspectos que deja fuera:** 
  - Este modelo representa solo el flujo de autorización y bloqueo de sala.
  - No modela notificaciones a estudiantes (futura funcionalidad).
  - No muestra detalles de cómo se comunica el mantenimiento con los estudiantes sobre sus reservas canceladas.
  - Asume que la reserva a cancelar es la que está confirmada en esa sala.

```mermaid
flowchart TD
    A[Usuario de Administrador bloquea esa sala] --> B[Sistema valida que la sala exista]
    B --> C{¿Usuario tiene rol de Administrador?}
    C -->|No| D[Sistema rechaza: sin permisos]
    D --> E[Sala y reservas no cambian]
    C -->|Sí| F{¿Sala existe en el sistema?}
    F -->|No| G[Sistema rechaza: sala no existe]
    G --> E
    F -->|Sí| H[Sistema busca la reserva<br/>confirmada en esa sala]
    H --> I[Sistema cambia estado de la reserva<br/>a POR_MANTENIMIENTO]
    I --> J[Sistema cambia estado de la sala<br/>a EN_MANTENIMIENTO]
    J --> K[Sistema registra motivo y fecha]
    K --> L[Sistema confirma bloqueo exitoso<br/>y lista reservas canceladas]
    E --> M[Fin]
    L --> M
```

---

## 4. Estados o efectos sobre los datos

**Entidades que se están modelando:** Sala y Reservas asociadas

| Entidad | Estado actual | Evento y condición | Estado siguiente | Efecto sobre los datos |
|---|---|---|---|---|
| Sala | DISPONIBLE o EN_USO | Bloqueo por Mantenimiento | EN_MANTENIMIENTO | Se registra el motivo del bloqueo y la fecha. La reserva se cancela automáticamente. |
| Reserva | CONFIRMADA | Pertenece a una sala que fue bloqueada | POR_MANTENIMIENTO | Se actualiza el estado. No se registra penalización al estudiante. Se conserva el motivo del bloqueo para referencia. |
| Reserva | CONFIRMADA | Intento de bloqueo SIN autorización | CONFIRMADA | No cambia nada. La sala permanece con su estado anterior. |

---

## 5. Trazabilidad

| Requisito de sesión 6 | Historia / caso de uso | Paso o rama del modelo | Escenario de aceptación relacionado |
|---|---|---|---|
| RES-RF-03 | RES-HU-02, RES-CU-02 | Rama principal (pasos 4–8) | **Normal:** Usuario Administrador bloquea sala B-102. Sistema cancela reserva de estudiante sin penalización. Resultado: Sala EN_MANTENIMIENTO, Reserva POR_MANTENIMIENTO. |
| RES-RF-03 | RES-CU-02 | E1 (paso 2, validación de permisos) | **Rechazo 1:** Usuario sin rol Administrador intenta bloquear. Sistema rechaza. Resultado: Sala sin cambios, reservas sin cambios. |
| RES-RF-03 | RES-CU-02 | E2 (paso 2, validación de existencia) | **Rechazo 2:** Usuario intenta bloquear sala no existente. Sistema rechaza. Resultado: No hay cambios en el sistema. |

---




## 6. Dudas y cambios en los requisitos

| Requisito | Duda o cambio | Estado / confirmación del cliente | Impacto |
|---|---|---|---|
| RES-RF-03 | ¿Se debe enviar una notificación automática (email/SMS) a los estudiantes cuyas reservas fueron canceladas por mantenimiento? | Pendiente de aclaración con Sergio | Afecta la poscondición: ¿el caso termina solo con log interno, o incluye comunicación a estudiantes? |
| RES-RF-03 | ¿Cuánto tiempo tarda la liberación de una sala? ¿Debe un operador desbloquearla manualmente o se auto-libera después de X horas? | Pendiente de aclaración con Sergio | Afecta la futura funcionalidad de desbloqueo. Por ahora, el modelo asume bloqueo manual hasta que Mantenimiento lo resuelve. |

---

## 7. Siguiente paso y participación

- **Tarea de desarrollo derivada del modelo:** Implementar en Django los modelos `Room` y `Reservation` con estados EN_MANTENIMIENTO y POR_MANTENIMIENTO, y crear la función `block_room_for_maintenance()` en `services.py` que busque y cancele automáticamente la reserva confirmada sin aplicar penalizaciones.
- **Requisito que la justifica:** RES-RF-03
- **Responsable inicial:** Sebastian Cruz (@Sebas0032)
- **Issue existente o nuevo, si corresponde:** Issue #17 — Implementar bloqueo de sala por Mantenimiento (Django ORM)
- **Aportes de cada integrante:**
  - **Luciana Soza:** Redacción de la historia RES-HU-02 y formulación de preguntas sobre notificaciones a estudiantes.
  - **Sebastian Cruz:** Desarrollo del caso de uso textual (flujo principal, E1 y E2) con validaciones de autorización claras.
  - **Sebastian Toledo:** Diseño del diagrama de actividad con decisión de permisos, tabla de estados de sala y reservas, y trazabilidad.
- **Asistencia de IA, si se utilizó:** 
  - **Herramienta:** Claude (asistente IA)
  - **Propósito:** Actualización del archivo sesion-07-modelos.md para cambiar de RES-RF-02 (cancelación) a RES-RF-03 (bloqueo).
  - **Aporte:** Adaptación de historia, caso de uso, diagrama mermaid y tabla de estados; incorporación de E1 y E2 para rechazos por permisos y sala inexistente.
  - **Verificación:** El equipo confirmó que el modelo cubre RES-RF-03 del sesion06.md, que incluye dos rutas de rechazo claras y que la poscondición especifica "sin penalización" (diferencia crítica con cancelación manual).

---

