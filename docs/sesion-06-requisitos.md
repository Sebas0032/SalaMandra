# Sesión 6 — Hallazgos y requisitos del proyecto

- Proyecto: SalaMandra — Sistema de Reserva de Salas de Estudio
- Integrantes: Luciana Soza (@luci-solar34), Sebastian Cruz (@Sebas0032), Sebastian Soto (@sebas-sst)
- Fecha: 01 de octubre de 2026
- Cliente o fuente consultada: Sergio Barrientos (Docente / Cliente)
- Flujo seleccionado: Gestión, modificación, cancelación y bloqueos de reservas de salas (PB-01 / PB-03 / PB-04)

## 1. Hallazgos de la entrevista

| ID | Pregunta | Respuesta o hallazgo | Fuente | Estado |
|---|---|---|---|---|
| ENT-01 | ¿Hasta cuánto tiempo antes se permite modificar una reserva? | Se permite modificar una reserva únicamente si falta al menos una hora para su inicio. Si falta menos de una hora o el horario ya comenzó, no se permite modificarla. | Sergio | Confirmado |
| ENT-02 | ¿Puede un estudiante cancelar una reserva sin penalización? | Se puede cancelar en cualquier momento antes de entrar en uso. Si se cancela con menos de 1 hora de anticipación, aplica penalización. La sanción es escalar: 1ra vez = bloqueo por 24 horas; 2da vez = 48 horas; 3ra vez = 1 semana; 4ta vez = todo el semestre. | Sergio | Confirmado |
| ENT-03 | ¿Se puede bloquear una sala para mantenimiento aunque haya reservas confirmadas y quién tiene ese permiso? | El Administrador y el Operante pueden bloquear un horario por mantenimiento únicamente antes de que empiece el turno. Si existen reservas confirmadas afectadas, se cancelan sin sanción y se notifica dentro del sistema. No se permite bloquear un turno ya iniciado. | Sergio | Confirmado |
| ENT-04 | ¿Todas las salas tienen los mismos horarios disponibles o cada sala puede tener horarios diferentes? | Los bloques A, B, C, D, E y F son la configuración inicial de referencia. El Administrador puede crear y configurar horarios, respetando una duración mínima de 2 horas, la separación de 15 minutos y las demás restricciones. | Sergio | Confirmado |
| ENT-05 | ¿Existe un intervalo de tiempo entre reservas para el desalojo? | Se define un intervalo de 15 minutos entre reservas para desalojo y limpieza. | Sergio | Confirmado |
| ENT-06 | ¿La información del solicitante se autocompleta desde la base de datos o se introduce manualmente? | Se autocompletan los datos del usuario desde la base de datos mediante su código institucional, considerando la incorporación de nuevos estudiantes durante el semestre. | Sergio | Confirmado |
| ENT-07 | ¿En qué condiciones se puede desbloquear manualmente un mantenimiento? | El Administrador o el Operante puede desbloquear manualmente un horario en mantenimiento **solo si la hora actual es anterior al inicio del bloque**. Una vez iniciado, el sistema rechaza el desbloqueo; no se produce liberación automática al finalizar el turno. Se registran el bloqueo, responsable y fecha de los desbloqueos válidos. | Sergio | Confirmado |
| ENT-08 | ¿Se pueden reservar horarios continuos? | No se permite reservar bloques horarios consecutivos (por ejemplo, A-B). Sí se permiten combinaciones no consecutivas, como A-C, A-D y C-E. | Sergio | Confirmado |
| ENT-09 | ¿El Administrador tiene la capacidad de penalizar manualmente a un estudiante? | Sí, el Administrador puede penalizar manualmente a un estudiante si no se presenta en la sala durante el horario reservado. Debe registrar obligatoriamente un comentario descriptivo. | Sergio | Confirmado |
| ENT-10 | ¿Se elimina el historial de sanciones al comenzar un semestre? | No. El contador de faltas se calcula automáticamente según los períodos semestrales definidos por el sistema. Al cambiar el período, el nuevo conteo parte de cero, sin borrar ni modificar el historial de sanciones, que permanece disponible para auditoría. | Sergio | Confirmado |
| ENT-11 | Si un estudiante tiene un bloqueo activo, ¿puede consultar las salas disponibles? | Puede consultar la disponibilidad de las salas, pero no puede realizar reservas mientras el bloqueo esté vigente. | Sergio | Confirmado |
| ENT-12 | ¿Con cuántos días u horas de anticipación un estudiante puede realizar una reserva? | Solo pueden reservarse horarios disponibles del día actual, desde las 00:00 de ese día y antes de la hora de finalización del bloque seleccionado; no se admiten reservas de días futuros ni de bloques ya finalizados. | Sergio | Confirmado |
| ENT-13 | ¿Qué días está permitido reservar salas? | No se permite realizar reservas los sábados, domingos ni feriados. | Sergio | Confirmado |
| ENT-14 | ¿Qué estados pueden tener las reservas a lo largo de su ciclo de vida? | Los estados de `Reserva` son `CONFIRMADA`, `CANCELADA` y `POR_MANTENIMIENTO`; los estados de `SalaHorario` son `DISPONIBLE` y `MANTENIMIENTO`. | Sergio | Confirmado |
| ENT-15 | ¿Qué sucede cuando llega la hora de finalización de una reserva? | Una vez finalizado el horario, la reserva deja de mostrarse en la lista de reservas activas y se pasa al siguiente bloque horario. | Sergio | Confirmado |
| ENT-16 | ¿Qué información debe registrar el solicitante sobre la actividad que realizará en la sala? | El solicitante debe seleccionar obligatoriamente el tipo de actividad que realizará en la sala mediante una lista desplegable con opciones como tutoría, examen, estudio, tarea o proyecto. No se permite dejar el campo vacío. | Sergio | Confirmado |
| ENT-17 | ¿Cada usuario debe tener un único rol o puede tener múltiples roles? | Cada usuario debe tener asignado un único rol dentro del sistema. No se permite asignar múltiples roles a una misma cuenta. | Sergio | Confirmado |
| ENT-18 | ¿Qué ocurre si un estudiante intenta modificar su reserva a un horario ya ocupado? | El sistema rechaza la modificación. La reserva original no se cancela ni se altera hasta que la modificación se confirme correctamente. Si el usuario desiste o el cambio falla, se conserva la reserva original. | Sergio | Confirmado |
| ENT-19 | ¿Qué operaciones puede realizar cada rol en el sistema? | **Solicitante:** crear, modificar y cancelar reservas. **Operante:** gestionar reservas en nombre de solicitantes y bloquear por mantenimiento y desbloquear manualmente sin liberación automática por fin de turno. **Administrador:** gestionar reservas, realizar cancelaciones administrativas sin sanción, bloquear/desbloquear por mantenimiento, crear salas y horarios, imponer y retirar sanciones; todas las acciones pertinentes se registran. | Sergio | Confirmado |
| ENT-20 | ¿Quiénes tienen la condición de solicitante? | Toda persona que cuente con un código institucional de la UPB puede ser solicitante. | Sergio | Confirmado |
| ENT-21 | ¿Las salas de estudio contemplan gestión de capacidad de personas? | No. Actualmente, las salas no tienen un límite ni una restricción de capacidad de personas. Esta característica queda fuera del alcance actual del sistema. | Sergio | Confirmado |
| ENT-22 | ¿Qué sucede con las reservas cuando una sala se bloquea por mantenimiento? | El bloqueo se registra sobre el horario seleccionado de una sala y mantiene ese horario en estado `MANTENIMIENTO` también en días posteriores, hasta un desbloqueo manual válido. Las reservas confirmadas afectadas pasan a `POR_MANTENIMIENTO` sin sanción y generan una notificación interna persistente con el motivo; no se envían correos. | Sergio | Confirmado |
| ENT-23 | ¿El sistema impide la creación de reservas en salas bloqueadas? | Sí, el sistema impide automáticamente que cualquier usuario realice una reserva en una sala durante los intervalos bloqueados por mantenimiento. | Sergio | Confirmado |

## 2. Alcance del flujo

- Incluye: Validación del tiempo de modificación (mínimo 1 hora antes); control de cancelaciones con penalización según bloque de 1 hora; registro y escala progresiva de sanciones a estudiantes (24h, 48h, 1 semana, todo el semestre); facultad de Administrador y Operante autorizado para bloquear intervalos por mantenimiento y mantenerlos bloqueados hasta su desbloqueo manual, además de gestionar las reservas afectadas, sin sancionar por mantenimiento.
- No incluye: confirmación de contraseñas en creación de cuentas (fuera del flujo de reservas de Sesión 06); pago o multas monetarias. Envíos de notificaciones por correo electrónico. Las notificaciones por cancelación debida a mantenimiento se muestran dentro de la página web del sistema e indican el motivo de la cancelación.

## 3. Requisitos

### [RES-RF-01 — Restricción de tiempo para modificación de reserva]

- **Tipo:** Funcional
- **Origen:** ENT-01 y encargo inicial
- **Prioridad y razón:** Alta, porque garantiza la previsibilidad del uso de las salas y evita modificaciones de último momento.
- **Estado:** Aprobado por el cliente
- **Requisito:** El sistema debe permitir modificar una reserva únicamente si la solicitud se realiza con al menos una hora de anticipación respecto a la hora de inicio. Si falta menos de una hora o la reserva ya comenzó, el sistema debe rechazar la modificación y conservar la reserva original sin cambios.
- **Criterio de aceptación o comprobación:**
  - **Situación inicial:** Existe una reserva confirmada para la sala A-101 a las 14:00.
  - **Acción:** El usuario intenta modificarla a las 13:15.
  - **Resultado esperado:** El sistema rechaza la modificación porque faltan menos de 60 minutos para el inicio. La reserva original permanece confirmada para las 14:00 en la sala A-101.

---

### [RES-RF-02 — Cancelación con sistema escalar de penalizaciones]

- **Tipo:** Funcional
- **Origen:** ENT-02
- **Prioridad y razón:** Alta, porque desincentiva las cancelaciones tardías y promueve la liberación oportuna de las salas.
- **Estado:** Aprobado por el cliente
- **Requisito:** El sistema debe permitir cancelar una reserva antes de que comience su uso. Si el estudiante cancela con menos de una hora de anticipación respecto al inicio, debe registrar una falta y aplicar una sanción según la siguiente escala: primera falta, bloqueo durante 24 horas; segunda falta, 48 horas; tercera falta, una semana; cuarta falta, el resto del semestre académico.
- **Criterio de aceptación o comprobación:**
  - **Situación inicial:** Un estudiante tiene una reserva confirmada para las 10:00 y no registra faltas previas durante el semestre.
  - **Acción:** Cancela la reserva a las 09:30.
  - **Resultado esperado:** El sistema cancela la reserva, registra la primera falta y aplica un bloqueo que impide crear nuevas reservas durante las siguientes 24 horas.
  - **Caso adicional:** Si cancela a las 08:00, cuando faltan exactamente dos horas, la reserva se cancela sin aplicar la sanción por cancelación tardía, siempre que no exista otra regla de bloqueo aplicable.

---

### [RES-RF-03 — Bloqueo y desbloqueo manual de sala por mantenimiento]

- **Tipo:** Funcional
- **Origen:** ENT-03, ENT-07, ENT-22 y ENT-23.
- **Prioridad y razón:** Alta, porque impide utilizar horarios bloqueados y asegura la trazabilidad de mantenimiento.
- **Estado:** Confirmado
- **Requisito:** El Administrador o el Operante autorizado puede bloquear por mantenimiento un horario de sala **solo antes de la hora de inicio de ese bloque**, registrando el motivo. El bloqueo se asocia al horario seleccionado de la sala y su estado `MANTENIMIENTO` **se mantiene también en días posteriores**, hasta un desbloqueo manual válido: el transcurso del tiempo o la finalización del turno no lo cambia automáticamente a `DISPONIBLE`. El desbloqueo manual **solo se permite cuando la hora actual es anterior a la hora de inicio del bloque**; si el turno ya empezó, se rechaza. Las reservas `CONFIRMADA` afectadas pasan a `POR_MANTENIMIENTO` sin sanción, y se notifica al solicitante dentro de la web con el motivo. Un desbloqueo no reactiva reservas canceladas.
- **Criterios de aceptación:**
  - **Bloqueo permitido:** Antes del inicio del turno, el Administrador u Operante selecciona una sala, el horario y el motivo; el sistema registra el bloqueo y el horario pasa a `MANTENIMIENTO`.
  - **Bloqueo rechazado:** Si la hora actual es igual o posterior al inicio del turno, el sistema rechaza el bloqueo y no modifica estados.
  - **Desbloqueo permitido:** Si la hora actual es anterior al inicio del bloque, un Administrador u Operante autorizado puede desbloquearlo; se registran responsable, fecha y bloqueo retirado, y vuelve a `DISPONIBLE` si no hay otra restricción.
  - **Desbloqueo rechazado:** Si el bloque ya comenzó, el sistema rechaza el desbloqueo manual, aunque el turno haya concluido.
  - **Persistencia:** Al finalizar el turno o cambiar de fecha, el horario sigue en `MANTENIMIENTO` si no se realizó un desbloqueo válido; no se habilita automáticamente.
  - **Reservas afectadas:** Una reserva confirmada afectada cambia a `POR_MANTENIMIENTO`, se genera aviso interno con el motivo y no se aplica sanción.
  - **Auditoría:** El bloqueo y cualquier desbloqueo válido se conservan como registros; el desbloqueo no restaura las reservas afectadas.

---

### [RES-RF-04 — Verificación de bloqueo de estudiante al intentar reservar]

- **Tipo:** Funcional
- **Origen:** ENT-02 y ENT-11
- **Prioridad y razón:** Alta, porque garantiza que las sanciones por cancelaciones tardías se apliquen efectivamente.
- **Estado:** Aprobado por el cliente
- **Requisito:** El sistema debe verificar si el solicitante tiene una sanción o un bloqueo vigente antes de confirmar una nueva reserva. Si existe un bloqueo activo, debe impedir la creación de la reserva e informar el motivo y el tiempo restante de la sanción. El usuario podrá seguir consultando las salas y sus horarios disponibles.
- **Criterio de aceptación o comprobación:**
  - **Situación inicial:** Un estudiante tiene un bloqueo de 24 horas que comenzó hace dos horas.
  - **Acción:** Intenta reservar una sala disponible.
  - **Resultado esperado:** El sistema rechaza la reserva, informa que el estudiante tiene una sanción activa y muestra el tiempo restante del bloqueo. El estudiante puede seguir consultando la disponibilidad de las salas.

---

### [RES-RF-05 — Validación del solicitante y autocompletado de datos]

- **Tipo:** Funcional
- **Origen:** ENT-06, ENT-20 
- **Prioridad y razón:** Alta ya que evita reservas asociadas a personas no registradas y reduce la introducción manual de datos.
- **Estado:** Aprobado 
- **Requisito:** El sistema debe permitir identificar al solicitante mediante su código universitario y completar automáticamente sus datos registrados. La validación debe consultar los datos vigentes, considerando que pueden incorporarse nuevos estudiantes durante el semestre.
- **Criterio de aceptación o comprobación:**
  - **Situación inicial:** El sistema consulta los datos del usuario.
  - **Acción:** Intenta crear una nueva reserva en cualquier sala disponible.
  - **Resultado esperado:** Se muestran los datos asociados al código sin necesidad de introducirlos manualmente.

---

### [RES-RF-06 — Creación de reservas]

- **Tipo:** Funcional
- **Origen:** ENT-12, ENT-19, ENT-20
- **Prioridad y razón:** Alta ya que permite realizar la función principal del sistema.
- **Estado:** Aprobado 
- **Requisito:** El sistema debe permitir que un usuario autorizado cree una reserva para una sala y un bloque horario disponible, respetando las reglas de calendario, disponibilidad, permisos y sanciones vigentes.
- **Criterio de aceptación o comprobación:**
  - **Situación inicial:** El solicitante está validado y la sala está disponible.
  - **Acción:** Selecciona la sala y el horario permitido y confirma la solicitud.
  - **Resultado esperado:** El sistema registra la reserva con un identificador y el estado correspondiente.
Otro caso
  - **Situación inicial:** La sala no está disponible.
  - **Acción:** El usuario intenta confirmar la reserva.
  - **Resultado esperado:** El sistema rechaza la solicitud sin generar una reserva duplicada.

---

### [RES-RF-07 — Creación de disponibilidad]

- **Tipo:** Funcional
- **Origen:** ENT-11, ENT-23
- **Prioridad y razón:** Alta ya que permite seleccionar horarios utilizables y evita solicitudes sobre bloques ocupados.
- **Estado:** Aprobado 
- **Requisito:** El sistema debe permitir consultar la disponibilidad de las salas según la fecha y los bloques horarios permitidos. Los usuarios sancionados podrán consultar las salas y horarios, pero NO realizar operaciones de reserva mientras el bloqueo de ese horario (por mantenimiento) o también por su sanción esté vigente.
- **Criterio de aceptación o comprobación:**
  - **Situación inicial:** Existen salas disponibles y ocupadas.
  - **Acción:** El usuario consulta la disponibilidad.
  - **Resultado esperado:** El sistema muestra los horarios según su estado.
Otro caso
  - **Situación inicial:** El usuario tiene una sanción vigente.
  - **Acción:** Consulta las salas e intenta reservar.
  - **Resultado esperado:** Puede consultar la disponibilidad, pero el sistema impide confirmar una reserva.

---

### [RES-RF-08 — Gestión de bloques horarios y calendario universitario]

- **Tipo:** Funcional
- **Origen:** ENT-04, ENT-05, ENT-08, ENT-13
- **Prioridad y razón:** Alta, ya que garantiza que las reservas respeten los horarios oficiales de la universidad y evita reservas consecutivas de un mismo solicitante.
- **Estado:** Confirmado
- **Requisito:** El sistema debe utilizar los horarios configurados para cada sala; los bloques A, B, C, D, E y F representan la configuración inicial de referencia y pueden ser configurados por el Administrador según RES-RF-20. Debe respetar un intervalo de 15 minutos para desalojo y limpieza entre reservas de una misma sala e impedir reservas los sábados, domingos y feriados. Además, un mismo solicitante no puede reservar bloques horarios consecutivos (A-B, B-C, C-D, etc.), independientemente de que elija la misma sala o salas diferentes. Se permiten bloques no consecutivos (por ejemplo, A-C, B-D o C-E), siempre que exista disponibilidad y se cumplan las demás reglas.
- **Configuración de feriados:** Las fechas no habilitadas por feriados se definen en la configuración del sistema, mediante `RESERVAS_FERIADOS` en `salamandra_project/settings.py`, usando el formato `AAAA-MM-DD`. El sistema consulta esta lista al validar la fecha de reserva. La configuración debe completarse con los feriados confirmados por la universidad.
- **Criterios de aceptación:**

  **Caso 1 — Intervalo entre reservas de distintos usuarios en una misma sala**
  - **Situación inicial:** La reserva de un solicitante en la sala A termina a las 09:45, al finalizar el bloque A.
  - **Acción:** Otro solicitante intenta reservar esa misma sala en el bloque B, que comienza a las 10:00.
  - **Resultado esperado:** El sistema puede aceptar la reserva porque existe un intervalo de 15 minutos entre ambos bloques, siempre que se cumplan las demás reglas de disponibilidad.

  **Caso 2 — Reserva en sábado, domingo o feriado**
  - **Situación inicial:** La fecha solicitada corresponde a un sábado, domingo o feriado registrado.
  - **Acción:** Un solicitante intenta crear una reserva.
  - **Resultado esperado:** El sistema rechaza la solicitud.

  **Caso 3 — Restricción de horarios consecutivos para un mismo solicitante**
  - **Situación inicial:** Un solicitante tiene una reserva confirmada en la sala A durante el bloque horario A, que finaliza a las 09:45.
  - **Acción:** El mismo solicitante intenta realizar otra reserva para el bloque horario B, que comienza a las 10:00, ya sea en la misma sala o en una diferente.
  - **Resultado esperado:** El sistema rechaza la solicitud porque el solicitante ya tiene una reserva en el bloque inmediatamente anterior. No se permiten reservas en horarios consecutivos para un mismo solicitante, independientemente de la sala seleccionada. Podrá reservar bloques no consecutivos, como A-C, B-D o C-E, siempre que cumpla los demás requisitos.

  **Caso 4 — Reserva en bloque no consecutivo**
  - **Situación inicial:** Un solicitante tiene una reserva confirmada en el bloque A de una sala.
  - **Acción:** El mismo solicitante solicita el bloque C, en esa sala o en otra diferente.
  - **Resultado esperado:** El sistema permite continuar con la solicitud, siempre que la sala elegida esté disponible y se cumplan las demás validaciones.

---

### [RES-RF-09 — Reservas de horarios disponibles del día actual]

- **Tipo:** Funcional
- **Origen:** ENT-12; aclaración del cliente.
- **Prioridad y razón:** Alta, porque delimita la ventana válida de reservas.
- **Estado:** Confirmado
- **Requisito:** El sistema permite crear reservas **únicamente para horarios disponibles correspondientes a la fecha actual**. La reserva puede solicitarse desde las **00:00 del mismo día** y debe confirmarse **antes de que finalice el bloque horario seleccionado**, siempre que se cumplan las demás restricciones de calendario, sanciones, disponibilidad y permisos. No se pueden reservar bloques de fechas futuras o pasadas ni bloques ya finalizados.
- **Criterios de aceptación:**
  - **Día futuro:** Un usuario intenta reservar mañana; el sistema rechaza la operación.
  - **Apertura:** Desde las 00:00, el usuario solicita un horario habilitado del día actual que todavía no ha terminado; el sistema permite continuar con las validaciones.
  - **Bloque finalizado:** El usuario intenta reservar un bloque del día actual cuya hora de finalización ya pasó; el sistema rechaza la solicitud.
  - **Bloque en mantenimiento:** Aunque sea hoy y el bloque no haya terminado, se rechaza si su estado es `MANTENIMIENTO`.
---

### [RES-RF-10 — Modificación segura de reservas]

- **Tipo:** Funcional
- **Origen:** ENT-01, ENT-18, ENT-19  
- **Prioridad y razón:** Alta ya que evita perder una reserva válida cuando una modificación no puede completarse.
- **Estado:** Confirmado
- **Requisito:** El sistema debe permitir modificar una reserva conforme a las restricciones temporales y de permisos. La reserva original debe conservarse hasta que la modificación se valide y confirme correctamente.
- **Criterios de aceptación:**
  - **Situación inicial:** Un usuario autorizado tiene una reserva confirmada.
  - **Acción:** Solicita cambiar a otra sala u horario disponible.
  - **Resultado esperado:** El sistema confirma el cambio y actualiza la reserva.
Otro caso:
  - **Situación inicial:** El nuevo horario está ocupado o la modificación no se confirma.
  - **Acción:** El usuario intenta completar el cambio.
  - **Resultado esperado:** El sistema rechaza la modificación y conserva intacta la reserva original.

---

### [RES-RF-11 — Estados de reservas y de horarios de salas]

- **Tipo:** Funcional
- **Origen:** ENT-14 y ENT-15; nomenclatura actual de la base de datos.
- **Prioridad y razón:** Alta, porque representa correctamente el ciclo de vida de cada entidad.
- **Estado:** Confirmado
- **Requisito:** El sistema debe distinguir los estados de **Reserva** (`CONFIRMADA`, `CANCELADA`, `POR_MANTENIMIENTO`) de los estados de **SalaHorario** (`DISPONIBLE`, `MANTENIMIENTO`). No debe utilizar `RESERVADA` ni `HABILITADO` como nombres de estado, ni incorporar `EN_USO` a los estados definidos. Una reserva finalizada no se muestra como vigente. Un horario en `MANTENIMIENTO` mantiene ese estado hasta su desbloqueo manual, sin habilitación por vencimiento del turno.
- **Criterios de aceptación:**
  - Al confirmar una reserva, su estado es `CONFIRMADA`.
  - Al cancelar ordinariamente una reserva, su estado es `CANCELADA`.
  - Si la reserva se cancela debido al mantenimiento, pasa a `POR_MANTENIMIENTO`.
  - Un horario sin mantenimiento está en `DISPONIBLE`, sujeto a las demás reglas de ocupación.
  - Al bloquearlo por mantenimiento, pasa a `MANTENIMIENTO` y permanece así hasta que un Administrador u Operante lo desbloquee explícitamente.
  - Cuando termina el horario de una reserva, deja de mostrarse como reserva vigente, pero no se agrega un estado `EN_USO`.
---

### [RES-RF-12 — Registro de la actividad prevista en la reserva]

- **Tipo:** Funcional
- **Origen:** ENT-16
- **Prioridad y razón:** Media porque permite identificar el propósito de uso de la sala.
- **Estado:** Confirmado
- **Requisito:** El sistema debe exigir que el solicitante seleccione el tipo de actividad que realizará durante la reserva mediante una lista desplegable con opciones como tutoría, examen, estudio, tarea o proyecto. La selección es obligatoria y no se permite confirmar la reserva si el campo está vacío.
- **Criterios de aceptación:**
  - **Situación inicial:** El usuario completa una solicitud de reserva.
  - **Acción:** Selecciona una actividad de la lista desplegable.
  - **Resultado esperado:** El sistema permite continuar si se cumplen las demás reglas de reserva.
  - **Situación inicial:** El usuario completa una solicitud de reserva sin seleccionar una actividad.
  - **Acción:** Intenta confirmar la reserva con el campo de actividad vacío.
  - **Resultado esperado:** El sistema rechaza la confirmación y solicita seleccionar una actividad de la lista desplegable.

---

### [RES-RF-13 — Administración de permisos y roles]

- **Tipo:** Funcional
- **Origen:** ENT-03, ENT-17, ENT-19, ENT-20 
- **Prioridad y razón:** Alta ya que limita las operaciones según las responsabilidades de cada usuario.
- **Estado:** Confirmado
- **Requisito:** El sistema debe asignar un único rol a cada usuario y autorizar exclusivamente las operaciones correspondientes a ese rol. El Operante puede crear, modificar y cancelar reservas en nombre de solicitantes identificados por su código institucional, así como bloquear horarios por mantenimiento y desbloquearlos manualmente conforme a sus permisos; nunca se desbloquean automáticamente por fin de turno. Las validaciones temporales, de sanciones y de disponibilidad también se aplican a las operaciones iniciadas por el Operante.
- **Criterios de aceptación:**
  - **Situación inicial:** Un usuario tiene rol de Solicitante.
  - **Acción:** Intenta bloquear una sala por mantenimiento.
  - **Resultado esperado:** El sistema rechaza la operación.
  - **Situación inicial:** Un usuario tiene rol de Administrador u Operante autorizado.
  - **Acción:** Bloquea una sala por mantenimiento.
  - **Resultado esperado:** El sistema permite la operación si se cumplen las demás validaciones, registra quién la realizó y cancela sin sanción las reservas afectadas.
  - **Situación inicial:** Existe un intervalo bloqueado por mantenimiento.
  - **Acción:** Un Administrador u Operante autorizado solicita desbloquearlo manualmente.
  - **Resultado esperado:** El sistema permite el desbloqueo únicamente si todavía no inició el bloque; registra al responsable y habilita el horario si no existe otra restricción. Si el bloque ya inició, rechaza la operación.
  - **Situación inicial:** Una cuenta ya tiene asignado el rol Operante.
  - **Acción:** Se intenta asignarle además el rol Administrador.
  - **Resultado esperado:** El sistema rechaza la asignación simultánea y mantiene un único rol para la cuenta.

---

### [RES-RF-14 — Aplicación manual de sanciones]

- **Tipo:** Funcional
- **Origen:** ENT-09 y ENT-19; aclaración del cliente.
- **Prioridad y razón:** Alta, porque permite aplicar sanciones y conservar su trazabilidad.
- **Estado:** Confirmado
- **Requisito:** El Administrador puede aplicar manualmente una sanción mediante una lista de opciones: **24 horas, 48 horas, una semana o semestre completo**, sin opción de un mes. Debe registrar un motivo obligatorio. Se conservan solicitante, duración, motivo, fecha y administrador responsable para auditoría.
- **Criterios de aceptación:**
  - El Administrador selecciona «1 semana», introduce el motivo y confirma; la sanción queda registrada y bloquea reservas durante su vigencia.
  - El Administrador puede elegir también 24 horas, 48 horas o semestre completo.
  - Si no introduce motivo, la operación se rechaza sin generar sanción.
  - No se presenta la opción «un mes».
---

### [RES-RF-15 — Conteo de sanciones por semestre y conservación del historial]

- **Tipo:** Funcional
- **Origen:** ENT-10; aclaración del cliente.
- **Prioridad y razón:** Alta, porque la escala debe calcularse para el semestre vigente sin perder los antecedentes.
- **Estado:** Confirmado
- **Requisito:** El sistema debe **calcular automáticamente el contador de faltas de cada solicitante según los períodos semestrales definidos por el sistema**. Al comenzar un nuevo semestre, el conteo correspondiente al nuevo período es cero y solo considera las faltas registradas dentro de las fechas del período correspondiente. **No se eliminan, reinician ni modifican los registros históricos de sanciones**: se conservan sus fechas, motivos, responsables, duraciones y retiros para trazabilidad, consultas y auditorías. El cálculo no requiere una tarea programada de reinicio ni una acción manual del Administrador.
- **Criterios de aceptación:**
  - **Situación inicial:** Un estudiante acumula tres faltas durante un período semestral definido por el sistema.
  - **Acción:** Comienza el siguiente semestre y el sistema consulta el contador del estudiante.
  - **Resultado esperado:** El contador del nuevo semestre comienza en cero y solo considera las faltas de ese período; las tres faltas anteriores no se contabilizan nuevamente.
  - El historial de sanciones de los semestres anteriores permanece conservado, consultable y sin alteraciones, incluyendo sus datos necesarios para auditoría.
  - La consulta del contador no elimina ni retira sanciones previas ni ejecuta una tarea de reinicio de base de datos.
---

### [RES-RF-16 — Prevención de reservas simultáneas incompatibles]

- **Tipo:** Funcional
- **Origen:** ENT-18, ENT-23 
- **Prioridad y razón:** Alta ya que evita que dos usuarios obtengan la misma sala para intervalos incompatibles.
- **Estado:** Confirmado
- **Requisito:** El sistema debe garantizar que dos solicitudes simultáneas incompatibles no puedan confirmar reservas para la misma sala y el mismo intervalo de tiempo.
- **Criterios de aceptación:**
  - **Situación inicial:** Dos usuarios solicitan la misma sala y el mismo bloque disponible prácticamente al mismo tiempo.
  - **Acción:** Ambas solicitudes intentan confirmarse.
  - **Resultado esperado:** Como máximo una solicitud se confirma; la otra se rechaza e informa que el horario ya no está disponible.

---

### [RES-RF-17 — Gestión de reservas afectadas por mantenimiento]

- **Tipo:** Funcional
- **Origen:** ENT-03, ENT-22, ENT-23.
- **Prioridad y razón:** Alta, para proteger las reservas afectadas y comunicar su cancelación.
- **Estado:** Confirmado
- **Requisito:** Cuando un Administrador u Operante bloquea **antes de su inicio** un horario de sala por mantenimiento, este pasa a `MANTENIMIENTO` y permanece bloqueado **hasta un desbloqueo manual**, sin liberarse automáticamente al terminar el turno. Las reservas `CONFIRMADA` afectadas pasan a `POR_MANTENIMIENTO`, sin sanción para sus titulares. Cada titular recibe una notificación dentro de la página web con el motivo del bloqueo, sin correo electrónico.
- **Criterios de aceptación:**
  - Bloquear un horario con reserva confirmada modifica la reserva a `POR_MANTENIMIENTO` y crea la notificación interna con el motivo.
  - Durante y después del turno, si no ha ocurrido un desbloqueo manual, el horario sigue en `MANTENIMIENTO`.
  - Solo se permite desbloquear antes de la hora de inicio del bloque; una vez iniciado, se rechaza. Un desbloqueo autorizado registra actor, fecha y bloqueo específico y nunca reactiva automáticamente las reservas afectadas.

---

### [RES-RF-18 — Operaciones asistidas por el Operante mediante código institucional]

- **Tipo:** Funcional
- **Origen:** ENT-06, ENT-19
- **Prioridad:** Alta
- **Estado:** Confirmado
- **Requisito:** El Operante debe autenticarse con su propia cuenta. Al elegir Crear, Modificar o Cancelar reserva, debe introducir el código institucional del solicitante; el sistema valida que exista, muestra sus datos y permite seleccionar la reserva o el horario pertinente. El código ingresado identifica al solicitante afectado, no sustituye la identidad autenticada del Operante. El sistema debe registrar la identidad del Operante responsable de cada operación realizada en nombre de un solicitante, junto con la fecha y hora de ejecución. Para bloquear por mantenimiento se seleccionan sala, intervalo y motivo, sin pedir código de solicitante. Para desbloquear se selecciona el horario bloqueado y se confirma la acción únicamente si todavía no ha llegado la hora de inicio del bloque. Si el bloque ya comenzó, se rechaza el desbloqueo.
- **Criterios de aceptación:**
  - Dado un código institucional válido, al seleccionar Crear reserva, el sistema autocompleta los datos del solicitante y aplica sus bloqueos y reglas de disponibilidad.
  - Dado un código inexistente, el sistema rechaza la operación sin alterar datos.
  - Para modificar o cancelar, el Operante debe seleccionar una reserva del solicitante indicado; no puede modificar una reserva de otra persona por error.
  - Para el bloqueo por mantenimiento, el sistema solicita sala, intervalo y motivo, y registra el Operante responsable.
  - Para el desbloqueo manual, el sistema exige que el bloque aún no haya comenzado y registra al responsable y la fecha y hora. Si ya inició, rechaza la solicitud.
  - Al crear, modificar o cancelar una reserva en nombre de un solicitante, el sistema registra la identidad del Operante y la fecha y hora de la operación.

### [RES-RF-19 — Advertencia y confirmación de cancelación tardía asistida]

- **Tipo:** Funcional (advertencia de interfaz vinculada a RES-RF-02)
- **Origen:** ENT-02, ENT-19
- **Prioridad:** Alta
- **Estado:** Confirmado
- **Requisito:** Si el Operante intenta cancelar en nombre de un solicitante una reserva que todavía no comenzó y faltan menos de 60 minutos, el sistema debe mostrar una advertencia explícita de que la operación generará una falta y que se aplicará la sanción conforme a las reglas vigentes. Debe permitir volver sin cancelar o confirmar conscientemente. Al confirmar, el servidor vuelve a validar las condiciones y registra cancelación y sanción de forma consistente. No se permite omitir la sanción por tener rol Operante.
- **Criterios de aceptación:**
  - Reserva a las 10:00, cancelación solicitada a las 09:30: se advierte que confirmar la cancelación generará una falta y una sanción conforme a las reglas vigentes, sin exigir que la advertencia detalle una duración exacta.
  - Si el Operante vuelve atrás, la reserva permanece intacta y no se registra sanción.
  - Si confirma, se cancela y sanciona al solicitante, registrando al Operante que realizó la acción.
  - Si la reserva ya comenzó, la cancelación se rechaza según RES-RF-02.
  - Si intenta modificar faltando menos de una hora, el sistema rechaza el cambio, sin permitir que una advertencia lo habilite.

---

### [RES-RF-20 — Creación administrativa de horarios con duración mínima y limpieza]

- **Tipo:** Funcional
- **Origen:** ENT-04, ENT-05 y ENT-19.
- **Prioridad:** Alta
- **Estado:** Confirmado
- **Requisito:** El Administrador puede crear salas y definir horarios para ellas; los bloques A–F son una configuración inicial de referencia y no horarios inmodificables. Cada horario debe durar **como mínimo 2 horas (120 minutos)** y debe existir un intervalo de **al menos 15 minutos** entre horarios sucesivos de una misma sala destinado al desalojo y limpieza. Se impiden horarios duplicados o superpuestos.
- **Criterios de aceptación:**
  - El Administrador crea dos horarios de 08:00 a 10:00 y de 10:15 a 12:15 para la misma sala: cumplen duración mínima e intervalo.
  - Un bloque de 08:00 a 10:30 es válido respecto de la duración mínima de dos horas.
  - Un bloque de 08:00 a 09:30 se rechaza porque dura menos de dos horas.
  - Si la separación entre bloques de una misma sala es de 5 minutos, el sistema rechaza la creación.
---

### [RES-RF-21 — Cancelación administrativa con trazabilidad y aviso]

- **Tipo:** Funcional
- **Origen:** Gestión administrativa de reservas.
- **Prioridad:** Alta
- **Estado:** Confirmado
- **Requisito:** El Administrador puede consultar y cancelar reservas confirmadas que aún no hayan comenzado sin sancionar al titular por esta cancelación administrativa. El sistema conserva la identidad del responsable y la fecha de la acción en auditoría y genera al titular una notificación visible dentro de la plataforma.
- **Criterios de aceptación:**
  - Ante una reserva confirmada para un turno futuro, el Administrador la cancela: se registra la cancelación sin sanción para el titular y se genera su aviso interno.
  - Ante una reserva ya comenzada, no se ofrece como cancelable por este flujo.

---

### [RES-RF-22 — Registro individual y único de desbloqueos]

- **Tipo:** Funcional
- **Origen:** ENT-07 y gestión de mantenimiento.
- **Prioridad:** Alta
- **Estado:** Confirmado
- **Requisito:** Cada desbloqueo manual registra el bloqueo específico retirado, quién lo retiró y en qué fecha y hora. Un bloqueo admite como máximo un desbloqueo. Solo el Administrador o el Operante puede ejecutarlo. El horario permanece en `MANTENIMIENTO` hasta que se ejecute un desbloqueo manual válido. El sistema solo permite desbloquear antes del inicio del turno y rechaza la operación desde el momento en que comienza, incluso si el turno ya finalizó. Sin un desbloqueo válido, el estado persiste en días posteriores.
- **Criterios de aceptación:**
  - Antes del inicio del bloque, el desbloqueo válido registra bloqueo, actor, fecha y hora; el estado cambia a `DISPONIBLE` si no existe otra restricción. Desde el inicio del bloque, se rechaza.
  - Intentar desbloquear dos veces el mismo bloqueo no genera un segundo registro.
  - La finalización del turno no genera ningún registro de desbloqueo ni cambia el estado por sí sola.
---

### [RES-RF-23 — Gestión persistente de notificaciones internas]

- **Tipo:** Funcional
- **Origen:** ENT-22 y gestión de notificaciones internas.
- **Prioridad:** Alta
- **Estado:** Confirmado
- **Requisito:** Los avisos de cancelación por mantenimiento y cancelación administrativa deben guardarse en la plataforma, mostrarse al destinatario y permitir que se marquen como leídos sin borrar su contenido. Para mantenimiento, el mensaje debe incluir el motivo registrado. No se envían correos electrónicos.
- **Criterios de aceptación:**
  - Si un turno reservado se bloquea por mantenimiento, se crea un aviso interno con el motivo y se conserva hasta después de consultarlo.
  - El solicitante marca el aviso como leído y el sistema conserva el registro, actualizando su indicador de lectura.

---

### [RES-RF-24 — Retiro administrativo de sanciones sin eliminación histórica]

- **Tipo:** Funcional
- **Origen:** Gestión administrativa de sanciones.
- **Prioridad:** Alta
- **Estado:** Confirmado
- **Requisito:** El Administrador puede retirar una sanción vigente sin borrar la sanción ni sus datos originales. Se registran la fecha y el usuario que realizó el retiro; la sanción histórica permanece consultable.
- **Criterios de aceptación:**
  - Al retirar una sanción vigente, deja de bloquear nuevas reservas y queda registrado el responsable del retiro.
  - No puede retirarse de nuevo una sanción ya retirada ni se elimina su historial.

---

### [RES-RF-25 — Advertencia de sanción en cancelaciones tardías]

- **Tipo:** Funcional
- **Origen:** RES-RF-02 y RES-RF-19.
- **Prioridad:** Alta
- **Estado:** Confirmado
- **Requisito:** Antes de confirmar una cancelación de una reserva no iniciada cuando faltan menos de 60 minutos, el sistema debe mostrar al solicitante o al Operante una advertencia general de que se generará una falta y se aplicará una sanción según las reglas vigentes, sin requerir que el aviso anticipe la duración exacta. Debe permitir **confirmar** o **volver atrás**. Las reglas se vuelven a comprobar al confirmar.
- **Criterios de aceptación:**
  - Al cancelar 30 minutos antes, aparece una advertencia general de que la operación implicará una falta y una sanción.
  - Si se elige volver atrás, la reserva y el historial de sanciones permanecen intactos.
  - Si se confirma, se registra la cancelación y sanción correspondiente una sola vez.

---

### [RES-RC-01 — Claridad en mensajes de penalización e impedimentos]

- Tipo: Calidad
- Origen: ENT-02, ENT-11, ENT-23
- Prioridad y razón: Media porque proporciona retroalimentación transparente al usuario sobre por qué no puede realizar la operación.
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
- Prioridad y razón: Alta ya que garantiza la integridad del modelo de datos e historial de sanciones dentro de la arquitectura elegida.
- Estado: Aprobado por el cliente
- Requisito: La lógica de sanciones, historial de cancelaciones y bloqueos de mantenimiento debe implementarse en Python y persistirse mediante los modelos de Django ORM.
- Criterio de comprobación posterior:
  - Situación inicial: Modelos ya previstos para realizar el caso.
  - Acción: Ejecutar la suite de pruebas unitarias sobre los métodos del servicio de cancelaciones y mantenimiento.
  - Resultado esperado: Las transacciones y actualización de estados se reflejan correctamente en la base de datos a través del ORM de Django.

## 4. Escenarios del flujo

| Caso | Requisito relacionado | Datos y acción | Resultado esperado |
|---|---|---|---|
| Normal | RES-RF-01 | Reserva confirmada a las 16:00. Solicitud de modificación enviada a las 14:30 (1 hora y 30 minutos antes). | El sistema aprueba la modificación, siempre que se cumplan las demás reglas, y actualiza el horario de la reserva. |
| Límite | RES-RF-01 | Reserva confirmada a las 16:00. Solicitud de modificación enviada a las 15:00 (exactamente 1 hora antes). | El sistema permite la modificación porque cumple el límite mínimo de una hora de anticipación. |
| Rechazo | RES-RF-02 | Reserva confirmada a las 12:00. El estudiante cancela a las 11:30 (30 minutos antes), siendo su primera falta del semestre. | El sistema cancela la reserva, registra la primera falta y bloquea al estudiante para realizar nuevas reservas durante 24 horas. |

Estos escenarios están cubiertos por pruebas automatizadas con `pytest`.

## 5. Participación y asistencia utilizada

- Aportes de cada integrante: 
  - Luciana Soza: Conducción de la entrevista al cliente, formulación de las preguntas sobre modificaciones y mantenimiento, y redacción de los hallazgos `ENT-01` y `ENT-03`.
  - Sebastian Cruz: Definición de los requisitos funcionales de penalizaciones escalar (`RES-RF-02`) y restricciones de tiempo (`RES-RF-01`), y configuración del Issue.
  - Sebastian Soto: Elaboración de criterios de aceptación, diseño de escenarios del flujo y redacción de la restricción técnica `RES-RT-01`.
- Asistencia de IA, si se utilizó: ChatGPT / Gemini para estructurar las respuestas de la entrevista en la plantilla estándar de la Sesión 6 de GitHub en formato Markdown.
