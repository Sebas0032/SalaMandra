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
| ENT-03 | ¿Se puede bloquear una sala para mantenimiento aunque haya reservas activas y quién tiene ese permiso? | Sí, únicamente el Administrador puede bloquear una sala por mantenimiento, incluso si está reservada o en uso. Las reservas que coincidan con el periodo de mantenimiento se cancelan. | Sergio | Confirmado |
| ENT-04 | ¿Todas las salas tienen los mismos horarios disponibles o cada sala puede tener horarios diferentes? | Se manejan bloques de horarios fijos (A, B, C, D, E, F), al igual que los horarios de clases de la universidad. | Sergio | Confirmado |
| ENT-05 | ¿Existe un intervalo de tiempo entre reservas para el desalojo? | Se define un intervalo de 15 minutos entre reservas para desalojo y limpieza. | Sergio | Confirmado |
| ENT-06 | ¿La información del solicitante se autocompleta desde la base de datos o se introduce manualmente? | Se autocompletan los datos del usuario desde la base de datos mediante su código institucional, considerando la incorporación de nuevos estudiantes durante el semestre. | Sergio | Confirmado |
| ENT-07 | ¿Cuando una sala está bloqueada puede igualmente el administrador desbloquearla manualmente o esperar que el horario del bloqueamiento acabe? | Espera el horario del bloqueamiento| Sergio | Confirmado |
| ENT-08 | ¿Se pueden reservar horarios continuos? | No se permite reservar bloques horarios consecutivos (por ejemplo, A-B). Sí se permiten combinaciones no consecutivas, como A-C, A-D y C-E. | Sergio | Confirmado |
| ENT-09 | ¿El Administrador tiene la capacidad de penalizar manualmente a un estudiante? | Sí, el Administrador puede penalizar manualmente a un estudiante si no se presenta en la sala durante el horario reservado. Debe registrar obligatoriamente un comentario descriptivo. | Sergio | Confirmado |
| ENT-10 | ¿Cuándo finaliza el semestre, se reinicia el historial de sanciones del estudiante? | Sí, el historial de sanciones se reinicia al comienzo de cada nuevo semestre. | Sergio | Confirmado |
| ENT-11 | Si un estudiante tiene un bloqueo activo, ¿puede consultar las salas disponibles? | Puede consultar la disponibilidad de las salas, pero no puede realizar reservas mientras el bloqueo esté vigente. | Sergio | Confirmado |
| ENT-12 | ¿Con cuántos días u horas de anticipación un estudiante puede realizar una reserva? | Se puede reservar con hasta 24 horas de antelación. Las reservas se habilitan a las 00:00 para ese mismo día. | Sergio | Confirmado |
| ENT-13 | ¿Qué días está permitido reservar salas? | No se permite realizar reservas los sábados, domingos ni feriados. | Sergio | Confirmado |
| ENT-14 | ¿Qué estados pueden tener las reservas a lo largo de su ciclo de vida? | Los estados indicados son: RESERVADA, EN USO, MANTENIMIENTO y HABILITADO. | Sergio | Confirmado |
| ENT-15 | ¿Qué sucede cuando llega la hora de finalización de una reserva? | Una vez finalizado el horario, la reserva deja de mostrarse en la lista de reservas activas y se pasa al siguiente bloque horario. | Sergio | Confirmado |
| ENT-16 | ¿Qué información debe registrar el solicitante sobre la actividad que realizará en la sala? | El solicitante puede seleccionar una actividad de una lista desplegable, como tutoría, examen, tarea o proyecto. El campo es opcional y puede dejarse vacío. | Sergio | Confirmado |
| ENT-17 | ¿Cada usuario debe tener un único rol o puede tener múltiples roles? | Un usuario puede tener asignados múltiples roles al mismo tiempo, por ejemplo, Administrador y Mantenimiento. | Sergio | Confirmado |
| ENT-18 | ¿Qué ocurre si un estudiante intenta modificar su reserva a un horario ya ocupado? | El sistema rechaza la modificación. La reserva original no se cancela ni se altera hasta que la modificación se confirme correctamente. Si el usuario desiste o el cambio falla, se conserva la reserva original. | Sergio | Confirmado |
| ENT-19 | ¿Qué operaciones puede realizar cada rol en el sistema? | **Solicitante:** crear, modificar y cancelar reservas. **Operador (becario):** crear y cancelar reservas. **Administrador:** crear, modificar y cancelar reservas; bloquear y desbloquear salas; crear horarios y aplicar sanciones manuales. | Sergio | Confirmado |
| ENT-20 | ¿Quiénes tienen la condición de solicitante? | Toda persona —estudiante, profesor o administrativo— que cuente con un código institucional de la UPB puede ser solicitante. | Sergio | Confirmado |
| ENT-21 | ¿Las salas de estudio contemplan gestión de capacidad de personas? | No. Actualmente, las salas no tienen un límite ni una restricción de capacidad de personas. Esta característica queda fuera del alcance actual del sistema. | Sergio | Confirmado |
| ENT-22 | ¿Qué sucede con las reservas cuando una sala se bloquea por mantenimiento? | Se bloquea únicamente el intervalo horario específico del mantenimiento. Las reservas que coincidan con ese periodo se cancelan automáticamente y se envía una notificación al usuario que las creó. | Sergio | Confirmado |
| ENT-23 | ¿El sistema impide la creación de reservas en salas bloqueadas? | Sí, el sistema impide automáticamente que cualquier usuario realice una reserva en una sala durante los intervalos bloqueados por mantenimiento. | Sergio | Confirmado |

## 2. Alcance del flujo

- Incluye: Validación del tiempo de modificación (mínimo 1 hora antes); control de cancelaciones con penalización según bloque de 1 hora; registro y escala progresiva de sanciones a estudiantes (24h, 48h, 1 semana, todo el semestre); facultad de rol de Administrador para cancelar reservas existentes y bloquear.
- No incluye: Pago o multas monetarias. Envíos automáticos de correos o notificaciones.

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

### [RES-RF-03 — Bloqueo de sala por mantenimiento y cancelación de reservas]

- **Tipo:** Funcional
- **Origen:** ENT-03, ENT-22 y ENT-23
- **Prioridad y razón:** Alta, porque permite atender contingencias de infraestructura e impide utilizar salas durante los periodos de mantenimiento.
- **Estado:** Aprobado por el cliente
- **Requisito:** El sistema debe permitir exclusivamente al Administrador bloquear una sala durante un intervalo específico por motivos de mantenimiento. Si existen reservas confirmadas que coincidan con dicho intervalo, el sistema debe cancelarlas automáticamente, cambiar su estado a `CANCELADA_POR_MANTENIMIENTO` y notificar a los usuarios afectados. Estas cancelaciones no deben generar sanciones por cancelación tardía.
- **Criterio de aceptación o comprobación:**
  - **Situación inicial:** La sala B-102 tiene una reserva confirmada para las 15:00 y se requiere bloquear ese intervalo por una fuga de agua.
  - **Acción:** El Administrador registra el bloqueo por mantenimiento.
  - **Resultado esperado:** La sala queda no disponible durante el intervalo bloqueado; la reserva afectada cambia a `CANCELADA_POR_MANTENIMIENTO`, se notifica al usuario y no se le aplica ninguna sanción por esa cancelación.

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
- **Prioridad y razón:** Alta ya que garantiza que las reservas respeten los horarios oficiales de la universidad.
- **Estado:** Pendiente de confirmación.
- **Requisito:** El sistema debe utilizar los bloques horarios definidos por la universidad, respetar un intervalo de 15 minutos para desalojo y limpieza entre reservas de una misma sala y evitar reservas en sábados, domingos y feriados.
- **Criterios de aceptación:**
  - **Situación inicial:** Una reserva termina a las 09:45 que es el horario A.
  - **Acción:** Otro usuario intenta reservar la misma sala a las 10:00 que es en el horario B.
  - **Resultado esperado:** El horario puede aceptarse si cumple las demás reglas de disponibilidad.
Otro caso:
  - **Situación inicial:** La fecha corresponde a un sábado, domingo o feriado registrado.
  - **Acción:** Un usuario intenta crear una reserva.
  - **Resultado esperado:** El sistema rechaza la solicitud.
Otro caso:
  - **Situación inicial:** Una reserva termina a las 09:45 que es el horario A.
  - **Acción:** El mismo usuario intenta reservar la misma sala a las 10:00 que es en el horario B.
  - **Resultado esperado:** El horario puede aceptarse ya que no se aceptan hacer reservas continuas (A-B) por el mismo usuario en diferentes salas. Solo puede hacer reservas en horarios A-C, B-D y así sucesivamente.

---

### [RES-RF-09 — Apertura de reservas con 24 horas de antelación]

- **Tipo:** Funcional
- **Origen:** ENT-12 
- **Prioridad y razón:** Alta porque controla cuándo se habilita la reserva de los bloques horarios.
- **Estado:** Pendiente de confirmación.
- **Requisito:** El sistema debe habilitar las reservas conforme a la ventana temporal acordada para cada día, permitiendo reservar desde las 00:00 del día correspondiente y hasta 24 horas antes, según la regla definitiva que confirme el cliente.
- **Criterios de aceptación:**
  - **Situación inicial:** Aún no ha llegado la apertura de reservas del día solicitado.
  - **Acción:** Un usuario intenta reservar anticipadamente.
  - **Resultado esperado:** El sistema impide la operación hasta la apertura autorizada.
Otro caso:
  - **Situación inicial:** Ha llegado la hora de la apertura.
  - **Acción:** Un usuario solicita un bloque disponible.
  - **Resultado esperado:** El sistema permite continuar con la validación de la reserva.

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

### [RES-RF-11 — Gestión de estados y visualización de reservas y salas]

- **Tipo:** Funcional
- **Origen:** ENT-14, ENT-15  
- **Prioridad y razón:** Alta por que permite representar la disponibilidad y el uso real de las salas.
- **Estado:**Confirmado.
- **Requisito:** El sistema debe reflejar los estados definidos para las salas y las reservas, y dejar de mostrar las reservas en la vista de horarios vigentes cuando haya terminado su intervalo de uso.
- **Criterios de aceptación:**
  - **Situación inicial:** Una reserva termina a las 12:00.
  - **Acción:** El usuario consulta las reservas vigentes a partir de las 12:00.
  - **Resultado esperado:** La reserva ya no aparece como una reserva vigente.

---

### [RES-RF-12 — Registro de la actividad prevista en la reserva]

- **Tipo:** Funcional
- **Origen:** ENT-16
- **Prioridad y razón:** Media porque permite identificar el propósito de uso de la sala.
- **Estado:** Confirmado
- **Requisito:** El sistema debe permitir que el solicitante seleccione el tipo de actividad que realizará durante la reserva, con opciones como tutoría, examen, estudio, tarea o proyecto. El campo debe poder dejarse vacío si el usuario no desea especificarlo.
- **Criterios de aceptación:**
  - **Situación inicial:** El usuario completa una solicitud de reserva.
  - **Acción:** Selecciona una actividad o deja el campo vacío.
  - **Resultado esperado:** El sistema permite continuar en ambos casos, siempre que se cumplan las demás reglas de reserva.

---

### [RES-RF-13 — Administración de permisos y roles]

- **Tipo:** Funcional
- **Origen:** ENT-03, ENT-17, ENT-19, ENT-20 
- **Prioridad y razón:** Alta ya que limita las operaciones según las responsabilidades de cada usuario.
- **Estado:** Confirmado
- **Requisito:** El sistema debe autorizar las operaciones según los roles asignados al usuario. Un usuario puede tener varios roles, y el sistema debe permitir únicamente las acciones autorizadas para cada uno.
- **Criterios de aceptación:**
  - **Situación inicial:** Un usuario tiene rol de Solicitante.
  - **Acción:** Intenta bloquear una sala por mantenimiento.
  - **Resultado esperado:** El sistema rechaza la operación.
  - **Situación inicial:** Un usuario tiene rol de Administrador.
  - **Acción:** Bloquea una sala por mantenimiento.
  - **Resultado esperado:** El sistema permite la operación si se cumplen las demás validaciones.

---

### [RES-RF-14 — Aplicación manual de sanciones]

- **Tipo:** Funcional
- **Origen:** ENT-09, ENT-19  
- **Prioridad y razón:** Alta porque permite registrar incumplimientos detectados durante la operación de las salas.
- **Estado:** Confirmado
- **Requisito:** El sistema debe permitir que el Administrador aplique manualmente una sanción a un solicitante y registre obligatoriamente el motivo de la sanción.
- **Criterios de aceptación:**
  - **Situación inicial:** El Administrador comprueba que un solicitante no se encuentra en la sala durante el horario reservado.
  - **Acción:** Registra una sanción manual.
  - **Resultado esperado:** El sistema guarda el solicitante, el motivo, el Administrador responsable y la fecha de aplicación.
  - **Nota:** La duración y la escala aplicable a las sanciones manuales deben confirmarse por separado.

---

### [RES-RF-15 — Reinicio semestral del historial de sanciones]

- **Tipo:** Funcional
- **Origen:** ENT-10  
- **Prioridad y razón:** Media; permite aplicar correctamente la escala de sanciones en cada periodo académico.
- **Estado:** Confirmado
- **Requisito:** El sistema debe reiniciar el contador utilizado para determinar la siguiente sanción al inicio de cada semestre académico.
- **Criterios de aceptación:**
  - **Situación inicial:** Un estudiante acumuló sanciones durante el semestre anterior.
  - **Acción:** Comienza un nuevo semestre académico.
  - **Resultado esperado:** El contador utilizado para determinar la próxima sanción se reinicia conforme a las reglas del periodo académico.
  - **Nota:** Debe definirse si el reinicio afecta únicamente al contador o también a los registros históricos. Se recomienda conservar el historial para auditoría.

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

### [RES-RF-17 — Gestión automática de reservas afectadas por mantenimiento]

- **Tipo:** Funcional
- **Origen:** ENT-03, ENT-22, ENT-23 
- **Prioridad y razón:** Alta porque evita que se utilicen salas durante los intervalos bloqueados.
- **Estado:** Confirmado
- **Requisito:** Cuando el Administrador bloquee un intervalo horario por mantenimiento, el sistema debe impedir nuevas reservas durante ese intervalo y gestionar automáticamente las reservas existentes que resulten afectadas. Debe notificarse al solicitante cuya reserva cambie de estado.
- **Criterios de aceptación:**
  - **Situación inicial:** Una sala tiene una reserva confirmada en el intervalo que se bloqueará por mantenimiento.
  - **Acción:** El Administrador registra el bloqueo.
  - **Resultado esperado:** El intervalo queda no disponible, la reserva afectada cambia al estado definitivo acordado, el solicitante recibe una notificación y no se aplica una sanción por cancelación.
  - **Nota:** Debe confirmarse si el bloqueo afecta exclusivamente al intervalo seleccionado y cuál será el estado definitivo de la reserva afectada.


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

Estos escenarios se integrarán en la suite de pruebas automatizadas con `pytest`.

## 5. Preguntas y decisiones pendientes

| Pregunta | AQuién consultar | Impacto mientras no se resuelva |
|---|---|---|
| ¿El período del semestre para la 4ta sanción tiene una fecha de reinicio automática al inicio del siguiente periodo académico? | Sergio (Cliente) | Afecta la lógica de expiración de las sanciones en la base de datos a largo plazo. |


## 6. Siguiente paso

- Tarea: Modelar las entidades `Sanction` en `models.py` de Django e implementar las funciones de cancelación tardía y bloqueo en `services.py`.
- Requisito relacionado: RES-RF-02 y RES-RF-03
- Responsable inicial: Sebastian Cruz (@Sebas0032)
- Issue: Issue #15 en el repositorio del proyecto en GitHub.

## 7. Participación y asistencia utilizada

- Aportes de cada integrante: 
  - Luciana Soza: Conducción de la entrevista al cliente, formulación de las preguntas sobre modificaciones y mantenimiento, y redacción de los hallazgos `ENT-01` y `ENT-03`.
  - Sebastian Cruz: Definición de los requisitos funcionales de penalizaciones escalar (`RES-RF-02`) y restricciones de tiempo (`RES-RF-01`), y configuración del Issue.
  - Sebastian Soto: Elaboración de criterios de aceptación, diseño de escenarios del flujo y redacción de la restricción técnica `RES-RT-01`.
- Asistencia de IA, si se utilizó: ChatGPT / Gemini para estructurar las respuestas de la entrevista en la plantilla estándar de la Sesión 6 de GitHub en formato Markdown.