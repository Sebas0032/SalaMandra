# Sesión 6 — Hallazgos y requisitos del proyecto

- Proyecto: SalaMandra — Sistema de Reserva de Salas de Estudio
- Integrantes: Luciana Soza (@luci-solar34), Sebastian Cruz (@Sebas0032), Sebastian Soto (@sebas-sst)
- Fecha: 01 de octubre de 2026
- Cliente o fuente consultada: Sergio Barrientos (Docente / Cliente)
- Flujo seleccionado: Gestión, modificación, cancelación y bloqueos de reservas de salas (PB-01 / PB-03 / PB-04)

## 1. Hallazgos de la entrevista

| ID | Pregunta | Respuesta o hallazgo | Fuente | Estado |
|---|---|---|---|---|
| ENT-01 | ¿Hasta cuánto tiempo antes se permite modificar una reserva? | El Solicitante y el Operante pueden modificar una reserva únicamente si falta al menos una hora para su inicio. El Administrador puede modificarla sin ese límite temporal, siempre que se cumplan las restantes validaciones. | Sergio | Confirmado |
| ENT-02 | ¿Puede un estudiante cancelar una reserva sin penalización? | Se puede cancelar en cualquier momento antes de entrar en uso. Si se cancela con menos de 1 hora de anticipación, aplica penalización. La sanción es escalonada: primera falta = bloqueo por 24 horas; segunda falta = 48 horas; tercera falta = una semana; cuarta falta = el resto del semestre. | Sergio | Confirmado |
| ENT-03 | ¿Se puede bloquear una sala para mantenimiento aunque haya reservas confirmadas y quién tiene ese permiso? | El Operante puede bloquear un horario de sala por mantenimiento antes del inicio del turno. El Administrador puede bloquear el horario sin aplicar la restricción temporal exigida al Operante, incluso después de que el turno haya comenzado o finalizado. El bloqueo se aplica a la asignación de sala y horario, permanece activo hasta un desbloqueo manual autorizado y no termina por el cambio de fecha ni por la finalización del turno. Las reservas confirmadas afectadas pasan a `POR_MANTENIMIENTO` sin sanción y se notifican internamente. | Sergio | Confirmado |
| ENT-04 | ¿Todas las salas tienen los mismos horarios disponibles o cada sala puede tener horarios diferentes? | Los bloques A, B, C, D, E y F corresponden a los horarios de referencia utilizados por el sistema. Las reservas deben respetar los horarios existentes y los intervalos de 15 minutos para desalojo y limpieza. | Sergio | Confirmado |
| ENT-05 | ¿Existe un intervalo de tiempo entre reservas para el desalojo? | Se define un intervalo de 15 minutos entre reservas para desalojo y limpieza. | Sergio | Confirmado |
| ENT-06 | ¿La información del solicitante se autocompleta desde la base de datos o se introduce manualmente? | Se autocompletan los datos del usuario desde la base de datos mediante su código institucional, considerando la incorporación de nuevos estudiantes durante el semestre. | Sergio | Confirmado |
| ENT-07 | ¿En qué condiciones se puede desbloquear manualmente un mantenimiento? | El Administrador y el Operante autorizado solo pueden desbloquear manualmente un horario en mantenimiento antes de la hora de inicio del bloque correspondiente a la fecha en que se registró el bloqueo. Una vez alcanzada esa hora, el sistema rechaza el desbloqueo, incluso en días posteriores. Un desbloqueo permitido devuelve el horario a `DISPONIBLE` y registra responsable, fecha y hora. El mantenimiento no vence automáticamente al terminar el turno. | Sergio | Confirmado |
| ENT-08 | ¿Se pueden reservar horarios continuos? | Un Solicitante no puede reservar bloques consecutivos (A-B); tampoco el Operante al gestionar sus reservas. El Administrador tiene una excepción de consecutividad al modificar reservas y al reservar para sí mismo, sin omitir la validación de ocupación y limpieza. | Sergio | Confirmado |
| ENT-09 | ¿El Administrador tiene la capacidad de penalizar manualmente a un estudiante? | Sí, el Administrador puede penalizar manualmente a un estudiante si no se presenta en la sala durante el horario reservado. Debe registrar obligatoriamente un comentario descriptivo. | Sergio | Confirmado |
| ENT-10 | ¿Se elimina el historial de sanciones al comenzar un semestre? | No. El contador de faltas se calcula automáticamente según los períodos semestrales definidos por el sistema. Al cambiar el período, el nuevo conteo parte de cero, sin borrar ni modificar el historial de sanciones, que permanece disponible para auditoría. | Sergio | Confirmado |
| ENT-11 | Si un estudiante tiene un bloqueo activo, ¿puede consultar las salas disponibles? | Puede consultar la disponibilidad de las salas, pero no puede realizar reservas mientras el bloqueo esté vigente. | Sergio | Confirmado |
| ENT-12 | ¿Con cuántos días u horas de anticipación un estudiante puede realizar una reserva? | Solo pueden reservarse horarios disponibles del día actual, desde las 00:00 de ese día y antes de la hora de finalización del bloque seleccionado; no se admiten reservas de días futuros ni de bloques ya finalizados. | Sergio | Confirmado |
| ENT-13 | ¿Qué días está permitido reservar salas? | No se permite realizar reservas los sábados, domingos ni en fechas incluidas en la configuración de feriados; estas fechas se determinan según el calendario universitario configurado. | Sergio | Confirmado |
| ENT-14 | ¿Qué estados pueden tener las reservas a lo largo de su ciclo de vida? | Los estados de `Reserva` son `CONFIRMADA`, `CANCELADA` y `POR_MANTENIMIENTO`; los de `SalaHorario` son `DISPONIBLE`, `MANTENIMIENTO` y `RETIRADO`. | Sergio | Confirmado |
| ENT-15 | ¿Qué sucede cuando llega la hora de finalización de una reserva? | Una vez finalizado el horario, la reserva deja de mostrarse en la lista de reservas activas y el sistema continúa mostrando los bloques horarios siguientes según disponibilidad. | Sergio | Confirmado |
| ENT-16 | ¿Qué información debe registrar el solicitante sobre la actividad que realizará en la sala? | El solicitante debe seleccionar obligatoriamente el tipo de actividad que realizará en la sala mediante una lista desplegable con las opciones Tutoría, Examen, Tarea y Proyecto. No se permite dejar el campo vacío. | Sergio | Confirmado |
| ENT-17 | ¿Cada usuario debe tener un único rol o puede tener múltiples roles? | Cada usuario debe tener asignado un único rol dentro del sistema. No se permite asignar múltiples roles a una misma cuenta. | Sergio | Confirmado |
| ENT-18 | ¿Qué ocurre si un estudiante intenta modificar su reserva a un horario ya ocupado? | El sistema rechaza la modificación. La reserva original no se cancela ni se altera hasta que la modificación se confirme correctamente. Si el usuario desiste o el cambio falla, se conserva la reserva original. | Sergio | Confirmado |
| ENT-19 | ¿Qué operaciones puede realizar cada rol en el sistema? | **Solicitante:** crear, modificar y cancelar reservas. **Operante:** gestionar reservas en nombre de solicitantes, bloquear horarios por mantenimiento antes de su inicio y desbloquearlos únicamente antes del inicio del bloque. **Administrador:** gestionar reservas con las excepciones autorizadas, bloquear horarios por mantenimiento sin la restricción temporal del Operante, incluso después de finalizar el turno, y desbloquearlos únicamente antes del inicio del bloque, además de gestionar sanciones y cuentas. Las acciones pertinentes se registran para auditoría. | Sergio | Confirmado |
| ENT-20 | ¿Quiénes tienen la condición de solicitante? | Toda persona precargada en el sistema con un código institucional válido y habilitada como Solicitante puede actuar como solicitante. | Sergio | Confirmado |
| ENT-21 | ¿Las salas de estudio contemplan gestión de capacidad de personas? | No. Actualmente, las salas no tienen un límite ni una restricción de capacidad de personas. Esta característica queda fuera del alcance actual del sistema. | Sergio | Confirmado |
| ENT-22 | ¿Qué sucede con las reservas cuando una sala se bloquea por mantenimiento? | El mantenimiento afecta la asignación de horario de una sala y continúa activo en fechas posteriores mientras no se realice un desbloqueo manual autorizado. Las reservas `CONFIRMADA` afectadas pasan a `POR_MANTENIMIENTO` sin sanción y generan una notificación interna persistente con el motivo. El desbloqueo no restablece automáticamente las reservas canceladas y se conserva el historial. | Sergio | Confirmado |
| ENT-23 | ¿El sistema impide la creación de reservas en salas bloqueadas? | Sí, el sistema impide automáticamente que cualquier usuario realice una reserva en una sala durante los intervalos bloqueados por mantenimiento. | Sergio | Confirmado |
| ENT-24 | ¿Puede el Administrador cancelar o modificar reservas iniciadas? | El Administrador tiene permisos especiales para cancelar reservas confirmadas ya iniciadas y modificar reservas sin el límite ordinario de 60 minutos, siempre que se superen las demás validaciones. | Reglas funcionales del sistema | Confirmado |
| ENT-25 | ¿Puede el Administrador reiniciar el conteo de sanciones y administrar cuentas? | El Administrador puede realizar un reinicio general manual del conteo de faltas sin eliminar el historial y activar o desactivar cuentas de solicitantes. | Gestión administrativa del sistema | Confirmado |

## 2. Alcance del flujo

- Incluye: Validación del tiempo de modificación (mínimo 1 hora antes); control de cancelaciones con penalización según bloque de 1 hora; registro y escala progresiva de sanciones a estudiantes (24h, 48h, 1 semana, todo el semestre); facultad de Administrador y Operante autorizado para bloquear y desbloquear manualmente horarios por mantenimiento, con persistencia del bloqueo hasta su retiro; cancelación administrativa sin sanciones; reinicio general de sanciones con historial preservado y gestión del estado de cuentas de solicitantes.
- No incluye: registro y autenticación de cuentas, incluida la confirmación de contraseña (funcionalidad existente que queda fuera del flujo analizado en esta sesión); pagos o multas monetarias; notificaciones por correo electrónico. Las notificaciones por cancelación debida a mantenimiento se muestran dentro de la página web del sistema e indican el motivo de la cancelación.

## 3. Requisitos

### [RES-RF-01 — Restricción de tiempo para modificación de reserva]

- **Tipo:** Funcional
- **Origen:** ENT-01 y encargo inicial
- **Prioridad y razón:** Alta, porque garantiza la previsibilidad del uso de las salas y evita modificaciones de último momento.
- **Estado:** Aprobado por el cliente
- **Requisito:** El sistema debe exigir al Solicitante y al Operante una anticipación mínima de una hora para modificar una reserva. El Administrador puede realizar modificaciones sin ese límite temporal, siempre que se verifiquen los permisos, la disponibilidad y las demás reglas aplicables. Una modificación rechazada conserva intacta la reserva original.
- **Criterio de aceptación o comprobación:**
  - **Situación inicial:** Existe una reserva confirmada de un Solicitante para la sala A-101 a las 14:00.
  - **Acción:** El Solicitante o el Operante que lo representa intenta modificarla a las 13:15.
  - **Resultado esperado:** El sistema rechaza la modificación porque faltan menos de 60 minutos para el inicio. La reserva original permanece confirmada para las 14:00 en la sala A-101.
  - **Caso administrativo:** Si el Administrador solicita modificar una reserva cuando faltan menos de 60 minutos, el sistema puede permitirlo si supera las restantes validaciones.

---

### [RES-RF-02 — Cancelación con sistema escalonado de penalizaciones]

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

### [RES-RF-03 — Bloqueo persistente y desbloqueo manual por mantenimiento]

- **Tipo:** Funcional
- **Origen:** ENT-03, ENT-07, ENT-22 y ENT-23.
- **Prioridad y razón:** Alta, porque impide realizar reservas en horarios que no se encuentran habilitados por mantenimiento y permite restablecerlos de manera controlada.
- **Estado:** Confirmado
- **Requisito:** El sistema debe permitir al Administrador y al Operante autorizado bloquear por mantenimiento una asignación de sala y horario, registrando obligatoriamente el motivo, el responsable y la fecha y hora de la operación. El Operante solo puede bloquear antes del inicio del turno; el Administrador puede bloquear sin la restricción temporal del Operante, incluso si el bloque ya comenzó o finalizó. El horario bloqueado pasa a `MANTENIMIENTO` y **permanece en ese estado hasta que se ejecute un desbloqueo manual válido**. Para ambos roles, el desbloqueo solo está permitido antes de la hora de inicio del bloque en la fecha de registro del mantenimiento; a partir de esa hora se rechaza, aunque el turno ya haya finalizado o haya cambiado el día. El fin del turno o el cambio de fecha no lo habilitan automáticamente. Mientras esté bloqueado, no se admiten nuevas reservas para esa asignación. Las reservas `CONFIRMADA` afectadas pasan a `POR_MANTENIMIENTO`, sin sanción para sus titulares, y se genera una notificación interna con el motivo. El desbloqueo no reactiva las reservas canceladas y todas las operaciones quedan registradas para auditoría.
- **Criterios de aceptación:**
  - **Bloqueo permitido:** El Operante bloquea un horario antes de su inicio; el sistema registra el motivo y responsable y cambia `SalaHorario` a `MANTENIMIENTO`.
  - **Restricción del Operante:** Si el horario ya comenzó, el sistema rechaza un nuevo bloqueo solicitado por el Operante.
  - **Permiso administrativo:** El Administrador puede bloquear un horario sin aplicar la restricción temporal exigida al Operante, incluso si el horario ya finalizó.
  - **Persistencia:** Al finalizar el turno o cambiar de fecha, el horario permanece en `MANTENIMIENTO` si no fue desbloqueado.
  - **Desbloqueo manual permitido:** Antes del inicio del bloque correspondiente a la fecha del bloqueo, un Administrador u Operante autorizado puede retirarlo; el sistema registra quién y cuándo lo hizo y cambia el horario a `DISPONIBLE`.
  - **Desbloqueo rechazado:** Desde el inicio del bloque, el sistema rechaza el retiro manual incluso después de finalizar el turno o en fechas posteriores; mientras no exista un desbloqueo válido, el horario permanece en `MANTENIMIENTO`.
  - **Reservas afectadas:** Las reservas confirmadas vinculadas al horario bloqueado cambian a `POR_MANTENIMIENTO`, se notifica el motivo y no se aplica sanción.
  - **Historial:** El desbloqueo no restaura reservas canceladas ni elimina la evidencia del bloqueo.

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
- **Prioridad y razón:** Alta, ya que evita reservas asociadas a personas no registradas y reduce la introducción manual de datos.
- **Estado:** Aprobado 
- **Requisito:** El sistema debe permitir identificar al solicitante mediante su código universitario y completar automáticamente sus datos registrados. La validación debe consultar los datos vigentes, considerando que pueden incorporarse nuevos estudiantes durante el semestre.
- **Criterio de aceptación o comprobación:**
  - **Situación inicial:** Existe un solicitante registrado con un código institucional válido.
  - **Acción:** El usuario autorizado introduce o selecciona ese código durante la creación de una reserva.
  - **Resultado esperado:** El sistema identifica al solicitante y muestra los datos registrados sin exigir su introducción manual.

---

### [RES-RF-06 — Creación de reservas]

- **Tipo:** Funcional
- **Origen:** ENT-12, ENT-19, ENT-20
- **Prioridad y razón:** Alta, ya que permite realizar la función principal del sistema.
- **Estado:** Aprobado 
- **Requisito:** El sistema debe permitir que un usuario autorizado cree una reserva para una sala y un bloque horario disponible, respetando las reglas de calendario, disponibilidad, permisos y sanciones vigentes.
- **Criterio de aceptación o comprobación:**
  - **Situación inicial:** El solicitante está validado y la sala está disponible.
  - **Acción:** Selecciona la sala y el horario permitido y confirma la solicitud.
  - **Resultado esperado:** El sistema registra la reserva con un identificador y el estado `CONFIRMADA`.
  **Caso adicional:**
  - **Situación inicial:** La sala no está disponible.
  - **Acción:** El usuario intenta confirmar la reserva.
  - **Resultado esperado:** El sistema rechaza la solicitud sin generar una reserva duplicada.

---

### [RES-RF-07 — Consulta de disponibilidad de salas y horarios]

- **Tipo:** Funcional
- **Origen:** ENT-11, ENT-23
- **Prioridad y razón:** Alta, ya que permite seleccionar horarios utilizables y evita solicitudes sobre bloques ocupados.
- **Estado:** Aprobado 
- **Requisito:** El sistema debe permitir consultar la disponibilidad de las salas según la fecha y los bloques horarios permitidos. La consulta muestra los horarios existentes, pero no crea ni habilita horarios. Los usuarios sancionados podrán consultar las salas y horarios, pero no podrán confirmar reservas mientras tengan una sanción vigente o el horario seleccionado se encuentre bloqueado.
- **Criterio de aceptación o comprobación:**
  - **Situación inicial:** Existen salas disponibles y ocupadas.
  - **Acción:** El usuario consulta la disponibilidad.
  - **Resultado esperado:** El sistema muestra los horarios según su estado.
  **Caso adicional:**
  - **Situación inicial:** El usuario tiene una sanción vigente.
  - **Acción:** Consulta las salas e intenta reservar.
  - **Resultado esperado:** Puede consultar la disponibilidad, pero el sistema impide confirmar una reserva.

---

### [RES-RF-08 — Gestión de bloques horarios y calendario universitario]

- **Tipo:** Funcional
- **Origen:** ENT-04, ENT-05, ENT-08, ENT-13
- **Prioridad y razón:** Alta, ya que garantiza que las reservas respeten los horarios oficiales de la universidad y evita reservas consecutivas de un mismo solicitante.
- **Estado:** Confirmado
- **Requisito:** El sistema debe utilizar los horarios configurados para cada sala; los bloques A, B, C, D, E y F representan la configuración de horarios de referencia del sistema. Debe respetar un intervalo mínimo de 15 minutos para desalojo y limpieza entre reservas de una misma sala e impedir reservas los sábados, domingos y en los feriados que se hayan configurado. Como regla general, un mismo solicitante no puede reservar bloques horarios consecutivos (A-B, B-C, C-D, etc.), en la misma sala ni en salas diferentes. El Administrador tiene una excepción a la restricción de consecutividad cuando modifica una reserva o crea una reserva para su propia cuenta, sin dispensar las demás validaciones. Se permiten bloques no consecutivos (por ejemplo, A-C, B-D o C-E), siempre que exista disponibilidad y se cumplan las demás reglas.
- **Configuración de feriados:** Las fechas no habilitadas por feriados se definen en la configuración del sistema, mediante `RESERVAS_FERIADOS` en `salamandra_project/settings.py`, usando el formato `AAAA-MM-DD`. El sistema consulta esta lista al validar la fecha de reserva. Las fechas de feriados deberán mantenerse actualizadas de acuerdo con el calendario universitario aplicable.
- **Criterios de aceptación:**

  **Caso 1 — Intervalo entre reservas de distintos usuarios en una misma sala (horarios predefinidos)**
  - **Situación inicial:** En la configuración inicial de bloques, la reserva de un solicitante en la sala A termina a las 09:45, al finalizar el bloque A.
  - **Acción:** Otro solicitante intenta reservar esa misma sala en el bloque B, que comienza a las 10:00.
  - **Resultado esperado:** El sistema puede aceptar la reserva porque existe un intervalo de 15 minutos entre ambos bloques, siempre que se cumplan las demás reglas de disponibilidad.

  **Caso 2 — Reserva en sábado, domingo o feriado**
  - **Situación inicial:** La fecha solicitada corresponde a un sábado, domingo o feriado registrado.
  - **Acción:** Un solicitante intenta crear una reserva.
  - **Resultado esperado:** El sistema rechaza la solicitud en sábado o domingo; para un feriado, la fecha debe figurar previamente en `RESERVAS_FERIADOS`.

  **Caso 3 — Restricción de horarios consecutivos para un mismo solicitante**
  - **Situación inicial:** En la configuración inicial de bloques, un solicitante tiene una reserva confirmada en la sala A durante el bloque horario A, que finaliza a las 09:45.
  - **Acción:** El mismo solicitante intenta realizar otra reserva para el bloque horario B, que comienza a las 10:00, ya sea en la misma sala o en una diferente.
  - **Resultado esperado:** El sistema rechaza la solicitud porque el solicitante ya tiene una reserva en el bloque inmediatamente anterior. No se permiten reservas en horarios consecutivos para un mismo solicitante, independientemente de la sala seleccionada. Podrá reservar bloques no consecutivos, como A-C, B-D o C-E, siempre que cumpla los demás requisitos. Esta restricción se mantiene para operaciones del Operante en nombre de solicitantes.

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
- **Prioridad y razón:** Alta, ya que evita perder una reserva válida cuando una modificación no puede completarse.
- **Estado:** Confirmado
- **Requisito:** El sistema debe permitir modificar una reserva conforme a las restricciones temporales y de permisos. La reserva original debe conservarse hasta que la modificación se valide y confirme correctamente.
- **Criterios de aceptación:**
  - **Situación inicial:** Un usuario autorizado tiene una reserva confirmada.
  - **Acción:** Solicita cambiar a otra sala u horario disponible.
  - **Resultado esperado:** El sistema confirma el cambio y actualiza la reserva.
  **Caso adicional:**
  - **Situación inicial:** El nuevo horario está ocupado o la modificación no se confirma.
  - **Acción:** El usuario intenta completar el cambio.
  - **Resultado esperado:** El sistema rechaza la modificación y conserva intacta la reserva original.

---

### [RES-RF-11 — Estados de reservas y horarios de salas]

- **Tipo:** Funcional
- **Origen:** ENT-14, ENT-15 y ENT-22.
- **Prioridad y razón:** Alta, porque distingue el ciclo de vida de las reservas del estado operativo de los horarios.
- **Estado:** Confirmado
- **Requisito:** Las reservas utilizan los estados `CONFIRMADA`, `CANCELADA` y `POR_MANTENIMIENTO`. Las asignaciones `SalaHorario` utilizan los estados `DISPONIBLE`, `MANTENIMIENTO` y `RETIRADO`. Un horario en `MANTENIMIENTO` conserva ese estado mientras no exista un desbloqueo manual válido, aunque finalice el turno o cambie la fecha. Un horario `RETIRADO` no puede ofertarse para reservas. Una reserva cuyo turno ya finalizó deja de mostrarse como vigente, sin necesidad de agregar un estado `EN_USO`.
- **Criterios de aceptación:**
  - Una nueva reserva se registra como `CONFIRMADA` y una cancelación ordinaria cambia su estado a `CANCELADA`.
  - Una reserva afectada por mantenimiento pasa a `POR_MANTENIMIENTO` y no se restaura automáticamente.
  - Al bloquear un horario, su estado cambia a `MANTENIMIENTO` y continúa así en días posteriores si no existe un desbloqueo manual.
  - Si el bloqueo se desbloquea antes del inicio del bloque en su fecha de registro, el horario vuelve a `DISPONIBLE` si se cumplen las demás condiciones; una vez iniciado el bloque, no se permite desbloquearlo.
  - Un horario `RETIRADO` no se ofrece para nuevas reservas y mantiene sus antecedentes registrados.

---

### [RES-RF-12 — Registro de la actividad prevista en la reserva]

- **Tipo:** Funcional
- **Origen:** ENT-16
- **Prioridad y razón:** Media, porque permite identificar el propósito de uso de la sala.
- **Estado:** Confirmado
- **Requisito:** El sistema debe exigir que el solicitante seleccione el tipo de actividad que realizará durante la reserva mediante una lista desplegable con las opciones Tutoría, Examen, Tarea y Proyecto. La selección es obligatoria y no se permite confirmar la reserva si el campo está vacío.
- **Criterios de aceptación:**
  - **Situación inicial:** El usuario completa una solicitud de reserva.
  - **Acción:** Selecciona Tutoría, Examen, Tarea o Proyecto de la lista desplegable.
  - **Resultado esperado:** El sistema permite continuar si se cumplen las demás reglas de reserva.
  - **Situación inicial:** El usuario completa una solicitud de reserva sin seleccionar una actividad.
  - **Acción:** Intenta confirmar la reserva con el campo de actividad vacío.
  - **Resultado esperado:** El sistema rechaza la confirmación y solicita seleccionar una actividad de la lista desplegable.

---

### [RES-RF-13 — Administración de permisos y roles]

- **Tipo:** Funcional
- **Origen:** ENT-03, ENT-17, ENT-19 y ENT-20
- **Prioridad y razón:** Alta, porque limita las operaciones según la responsabilidad de cada usuario.
- **Estado:** Confirmado
- **Requisito:** El sistema debe asignar un único rol a cada usuario y permitir exclusivamente las operaciones correspondientes a él. El Operante puede crear, modificar y cancelar reservas en nombre de solicitantes identificados por su código institucional; también puede bloquear horarios por mantenimiento antes de su inicio y desbloquearlos únicamente antes del inicio del bloque correspondiente a la fecha del bloqueo. El Administrador dispone de las excepciones autorizadas para reservas y puede bloquear un horario por mantenimiento incluso después de que el turno haya finalizado. Ningún mantenimiento se libera automáticamente al terminar el turno. Las validaciones de sanciones, disponibilidad y permisos se aplican también a operaciones iniciadas por el Operante. El Administrador puede activar o desactivar cuentas de solicitantes, conservando su historial.
- **Criterios de aceptación:**
  - Un Solicitante intenta bloquear un horario por mantenimiento: el sistema rechaza la operación.
  - El Operante intenta bloquear un horario iniciado: el sistema rechaza la operación.
  - El Administrador solicita bloquear un horario que ya comenzó o finalizó: la operación no se rechaza por el tiempo transcurrido, y se registran las reservas confirmadas afectadas sin sanción, siempre que se cumplan las demás validaciones.
  - Un Administrador u Operante autorizado solicita desbloquear antes del inicio del bloque en la fecha de registro del bloqueo: se registra el responsable y el horario vuelve a `DISPONIBLE` si no existen otras restricciones. Después de esa hora, se rechaza la acción.
  - Una cuenta con rol Operante intenta recibir simultáneamente el rol Administrador: el sistema rechaza la asignación adicional.
  - El Administrador desactiva o reactiva una cuenta de Solicitante sin eliminar sus datos históricos.

---

### [RES-RF-14 — Aplicación manual de sanciones]

- **Tipo:** Funcional
- **Origen:** ENT-09 y ENT-19; aclaración del cliente.
- **Prioridad y razón:** Alta, porque permite aplicar sanciones y conservar su trazabilidad.
- **Estado:** Confirmado
- **Requisito:** El Administrador puede aplicar manualmente una sanción mediante una lista de opciones: **24 horas, 48 horas, una semana o semestre completo**, sin opción de un mes. Debe registrar un motivo obligatorio. Se conservan el solicitante, el tipo de sanción, la fecha de inicio, la fecha de finalización, el motivo y el Administrador responsable para auditoría. Para la sanción de semestre completo no existe una duración fija en horas; su fecha de finalización corresponde al siguiente corte semestral (1 de enero o 1 de julio).
- **Criterios de aceptación:**
  - El Administrador selecciona «1 semana», introduce el motivo y confirma; la sanción queda registrada y bloquea reservas durante su vigencia.
  - El Administrador puede elegir también 24 horas, 48 horas o semestre completo; en este último caso, el bloqueo termina en el siguiente corte semestral y no se representa como una cantidad fija de horas.
  - Si no introduce motivo, la operación se rechaza sin generar sanción.
  - No se presenta la opción «un mes».

---

### [RES-RF-15 — Conteo de sanciones por semestre y conservación del historial]

- **Tipo:** Funcional
- **Origen:** ENT-10 y ENT-25.
- **Prioridad y razón:** Alta, porque la escala debe calcularse para el semestre vigente sin perder los antecedentes.
- **Estado:** Confirmado
- **Requisito:** El sistema debe **calcular automáticamente el contador de faltas de cada solicitante según semestres de calendario**: del 1 de enero al 30 de junio y del 1 de julio al 31 de diciembre. El Administrador también puede realizar un reinicio manual general del conteo de faltas, registrando la operación y retirando las sanciones vigentes sin borrar el historial. Al comenzar un nuevo semestre, el conteo correspondiente al nuevo período es cero y solo considera las faltas registradas dentro de las fechas del período correspondiente. **No se eliminan los registros históricos de sanciones**: sus datos originales se conservan y cualquier retiro o reinicio administrativo queda registrado para trazabilidad, consultas y auditorías. El cambio semestral no requiere una tarea programada ni una acción manual; el reinicio administrativo es una operación extraordinaria y explícita.
- **Criterios de aceptación:**
  - **Situación inicial:** Un estudiante acumula tres faltas durante un período semestral definido por el sistema.
  - **Acción:** Comienza el siguiente semestre y el sistema consulta el contador del estudiante.
  - **Resultado esperado:** El contador del nuevo semestre comienza en cero y solo considera las faltas de ese período; las tres faltas anteriores no se contabilizan nuevamente.
  - El historial de sanciones de los semestres anteriores permanece conservado en la base de datos, sin borrar los datos originales necesarios para auditoría.
  - La consulta del contador no elimina sanciones previas ni ejecuta una tarea de reinicio de base de datos.
  - Si el Administrador realiza un reinicio general manual, el sistema registra fecha y responsable, fija el nuevo corte de conteo y retira las sanciones vigentes; el historial se conserva para auditoría.

---

### [RES-RF-16 — Prevención de reservas simultáneas incompatibles]

- **Tipo:** Funcional
- **Origen:** ENT-18, ENT-23 
- **Prioridad y razón:** Alta, ya que evita que dos usuarios obtengan la misma sala para intervalos incompatibles.
- **Estado:** Confirmado
- **Requisito:** El sistema debe garantizar que dos solicitudes simultáneas incompatibles no puedan confirmar reservas para la misma sala y el mismo intervalo de tiempo.
- **Criterios de aceptación:**
  - **Situación inicial:** Dos usuarios solicitan la misma sala y el mismo bloque disponible prácticamente al mismo tiempo.
  - **Acción:** Ambas solicitudes intentan confirmarse.
  - **Resultado esperado:** Como máximo una solicitud se confirma; la otra se rechaza e informa que el horario ya no está disponible.

---

### [RES-RF-17 — Gestión de reservas afectadas por mantenimiento]

- **Tipo:** Funcional
- **Origen:** ENT-03, ENT-22 y ENT-23.
- **Prioridad y razón:** Alta, porque protege a los titulares de reservas canceladas por mantenimiento y asegura su notificación.
- **Estado:** Confirmado
- **Requisito:** Al registrar un bloqueo por mantenimiento, el sistema debe identificar las reservas `CONFIRMADA` asociadas a la asignación de sala y horario bloqueada, cambiar su estado a `POR_MANTENIMIENTO` sin sancionar a sus titulares y crear una notificación interna persistente que indique el motivo. El horario permanece en `MANTENIMIENTO` hasta su desbloqueo manual, incluso en días posteriores. El desbloqueo no restablece automáticamente las reservas afectadas ni elimina sus notificaciones o el historial.
- **Criterios de aceptación:**
  - Al bloquear una asignación de sala y horario con reservas confirmadas, estas pasan a `POR_MANTENIMIENTO` y sus titulares reciben una notificación con el motivo.
  - El bloqueo impide realizar nuevas reservas en ese horario mientras permanezca en `MANTENIMIENTO`.
  - Al finalizar el turno, el mantenimiento permanece activo si nadie lo desbloquea.
  - Tras el desbloqueo manual, las reservas afectadas continúan en `POR_MANTENIMIENTO` y las notificaciones se conservan.

---

### [RES-RF-18 — Operaciones asistidas por el Operante mediante código institucional]

- **Tipo:** Funcional
- **Origen:** ENT-06 y ENT-19
- **Prioridad:** Alta
- **Estado:** Confirmado
- **Requisito:** El Operante debe autenticarse con su propia cuenta. Para crear, modificar o cancelar reservas en nombre de un solicitante, introduce el código institucional de este; el sistema comprueba su existencia, muestra sus datos y permite seleccionar la reserva o el horario aplicable. La identidad del Operante permanece diferenciada de la del solicitante y se registra junto con la fecha y hora de cada operación. Para bloquear por mantenimiento se selecciona sala, horario y motivo, sin requerir código de solicitante. Para desbloquear se selecciona el bloqueo activo y se confirma su retiro por un usuario autorizado, siempre que la hora actual sea anterior al inicio del bloque correspondiente a la fecha del bloqueo. Los bloqueos no vencen automáticamente.
- **Criterios de aceptación:**
  - Con un código institucional válido, el sistema muestra los datos del solicitante y aplica sus restricciones de sanciones y disponibilidad.
  - Con un código inexistente, la operación se rechaza sin alterar datos.
  - Para modificar o cancelar, el Operante selecciona una reserva del titular indicado.
  - Para bloquear por mantenimiento, selecciona sala, horario y motivo; el sistema comprueba los permisos temporales del Operante y registra quién realizó la acción.
  - Para desbloquear, selecciona un bloqueo activo antes del inicio del bloque en la fecha de registro del bloqueo; el sistema registra responsable y fecha de la operación. Una vez comenzado, rechaza el desbloqueo.
  - En toda creación, modificación o cancelación asistida se registra la identidad del Operante y el momento de la acción.

---

### [RES-RF-19 — Advertencia y confirmación de cancelación tardía asistida]

- **Tipo:** Funcional (advertencia de interfaz vinculada a RES-RF-02)
- **Origen:** ENT-02, ENT-19
- **Prioridad:** Alta
- **Estado:** Confirmado como requisito
- **Requisito:** Si el Operante intenta cancelar en nombre de un solicitante una reserva que todavía no comenzó y faltan menos de 60 minutos, el sistema debe mostrar una advertencia explícita de que la operación generará una falta y que se aplicará la sanción conforme a las reglas vigentes. Antes de ejecutar la cancelación, el Operante debe poder revisar la advertencia y decidir si continúa o abandona la operación. Al confirmar, el servidor vuelve a validar las condiciones y registra cancelación y sanción de forma consistente. No se permite omitir la sanción por tener rol Operante.
- **Criterios de aceptación:**
  - Reserva a las 10:00, cancelación solicitada a las 09:30: se advierte que confirmar la cancelación generará una falta y una sanción conforme a las reglas vigentes, sin exigir que la advertencia detalle una duración exacta.
  - Si el Operante abandona la operación sin enviarla, la reserva permanece intacta y no se registra sanción.
  - Si el Operante confirma la cancelación desde la pantalla asistida, se cancela y sanciona al solicitante, registrando al Operante que realizó la acción.
  - Si la reserva ya comenzó, la cancelación se rechaza según RES-RF-02.
  - Si intenta modificar faltando menos de una hora, el sistema rechaza el cambio, sin permitir que una advertencia lo habilite.

---

### [RES-RF-20 — Cancelación administrativa con trazabilidad y aviso]

- **Tipo:** Funcional
- **Origen:** Gestión administrativa de reservas.
- **Prioridad:** Alta
- **Estado:** Confirmado
- **Requisito:** El Administrador puede consultar y cancelar reservas confirmadas incluso si el turno ya comenzó, sin sancionar al titular por esta cancelación administrativa. El sistema conserva la identidad del responsable y la fecha de la acción en auditoría y genera al titular una notificación visible dentro de la plataforma.
- **Criterios de aceptación:**
  - Ante una reserva confirmada para un turno futuro, el Administrador la cancela: se registra la cancelación sin sanción para el titular y se genera su aviso interno.
  - Ante una reserva confirmada cuyo turno ya comenzó, el Administrador puede cancelarla sin sancionar al titular, registrando la acción.

---

### [RES-RF-21 — Desbloqueo manual y conservación del historial de mantenimiento]

- **Tipo:** Funcional
- **Origen:** ENT-07 y gestión de mantenimiento.
- **Prioridad:** Alta
- **Estado:** Confirmado
- **Requisito:** Cada bloqueo por mantenimiento debe quedar asociado a la asignación de sala y horario afectada y conservar su motivo, responsable y fecha de registro. El Administrador o el Operante autorizado puede retirar manualmente un bloqueo activo **solo antes del inicio del bloque correspondiente a la fecha del bloqueo**. Una vez iniciado el bloque, el sistema impide su desbloqueo aunque hayan transcurrido otros días. Cada bloqueo admite **como máximo un registro de desbloqueo**, que identifica al bloqueo retirado, al usuario responsable y el momento de la operación. Si no se realiza un desbloqueo, el horario continúa en `MANTENIMIENTO` sin importar la finalización del turno o el cambio de fecha. Un desbloqueo permitido devuelve el horario a `DISPONIBLE` cuando no exista otra restricción; no recupera las reservas canceladas.
- **Criterios de aceptación:**
  - Un usuario autorizado desbloquea un horario en `MANTENIMIENTO` antes del inicio del bloque en la fecha de registro del bloqueo: se registra el desbloqueo, responsable y fecha y hora.
  - Si el bloque ya comenzó o finalizó, el sistema rechaza el desbloqueo, incluso en días posteriores.
  - Un segundo intento de desbloquear el mismo bloqueo no genera un registro duplicado.
  - Al terminar el turno, el estado `MANTENIMIENTO` no cambia automáticamente.
  - Si el horario continúa bloqueado al día siguiente, no permite nuevas reservas y, al haber pasado el inicio del bloque original, el desbloqueo manual se rechaza con la regla actual.
  - El historial de bloqueos y desbloqueos permanece disponible para auditoría.

---

### [RES-RF-22 — Gestión persistente de notificaciones internas]

- **Tipo:** Funcional
- **Origen:** ENT-22 y gestión de notificaciones internas.
- **Prioridad:** Alta
- **Estado:** Confirmado
- **Requisito:** Los avisos de cancelación por mantenimiento y cancelación administrativa deben guardarse en la plataforma, mostrarse al destinatario y permitir que se marquen como leídos sin borrar su contenido. Para mantenimiento, el mensaje debe incluir el motivo registrado. No se envían correos electrónicos.
- **Criterios de aceptación:**
  - Si un turno reservado se bloquea por mantenimiento, se crea un aviso interno con el motivo y se conserva hasta después de consultarlo.
  - El solicitante marca el aviso como leído y el sistema conserva el registro, actualizando su indicador de lectura.

---

### [RES-RF-23 — Retiro administrativo de sanciones sin eliminación histórica]

- **Tipo:** Funcional
- **Origen:** Gestión administrativa de sanciones y ENT-25.
- **Prioridad:** Alta
- **Estado:** Confirmado
- **Requisito:** El Administrador puede retirar una sanción vigente sin borrar sus datos originales. Se registran la fecha y el usuario que realizó el retiro; la sanción histórica permanece almacenada en la base de datos para trazabilidad y auditoría.
- **Criterios de aceptación:**
  - Al retirar una sanción vigente, deja de bloquear nuevas reservas y queda registrado el responsable del retiro.
  - No puede retirarse de nuevo una sanción ya retirada ni se elimina su historial.

---

### [RES-RF-24 — Advertencia de sanción para el Solicitante en cancelaciones tardías]

- **Tipo:** Funcional
- **Origen:** RES-RF-02 y RES-RF-19.
- **Prioridad:** Alta
- **Estado:** Confirmado como requisito
- **Requisito:** Antes de que el Solicitante confirme la cancelación de una reserva no iniciada cuando faltan menos de 60 minutos, el sistema debe mostrarle una advertencia general de que se generará una falta y se aplicará una sanción según las reglas vigentes, sin requerir que el aviso anticipe la duración exacta. Para cancelaciones asistidas por el Operante se aplica RES-RF-19. Debe permitir **confirmar** o **volver atrás**. Las reglas se vuelven a comprobar al confirmar.
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
- Requisito: Ante el rechazo de una operación por penalización o bloqueo de mantenimiento, el sistema debe mostrar un mensaje explicativo detallado con el motivo del rechazo y, cuando se trate de una sanción temporal, su fecha de finalización o tiempo restante.
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
| Cancelación tardía | RES-RF-02 | Reserva confirmada a las 12:00. El estudiante cancela a las 11:30 (30 minutos antes), siendo su primera falta del semestre. | El sistema cancela la reserva, registra la primera falta y bloquea al estudiante para realizar nuevas reservas durante 24 horas. |

El proyecto contiene pruebas automatizadas con `pytest` relacionadas con modificaciones, cancelaciones, sanciones y mantenimiento. La ejecución y los resultados de las pruebas deben verificarse en el entorno del proyecto.

## 5. Participación y asistencia utilizada

- Aportes de cada integrante: 
  - Luciana Soza: Conducción de la entrevista al cliente, formulación de las preguntas sobre modificaciones y mantenimiento, y redacción de los hallazgos `ENT-01` y `ENT-03`.
  - Sebastian Cruz: Definición de los requisitos funcionales de penalizaciones escalonadas (`RES-RF-02`) y restricciones de tiempo (`RES-RF-01`), y configuración del Issue.
  - Sebastian Soto: Elaboración de criterios de aceptación, diseño de escenarios del flujo y redacción de la restricción técnica `RES-RT-01`.
- Asistencia de IA, si se utilizó: ChatGPT / Gemini para estructurar las respuestas de la entrevista en la plantilla estándar de la Sesión 6 de GitHub en formato Markdown.
