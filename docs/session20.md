# Sesión 20 — Recorridos de interacción del sistema

Cada recorrido utiliza cuatro campos: **Persona → Presentación → Lógica → Resultado**. La persona inicia la acción, la presentación recibe sus datos, la lógica aplica las reglas y la presentación comunica el resultado. Los rechazos no deben dejar cambios parciales.

Las referencias a la presentación incluyen el HTML y la vista que lo atiende. Los recorridos cubren las funciones actuales seleccionadas para esta sesión; la gestión de salas y horarios corresponde a futuros alcances.

Documentación relacionada: [arquitectura general](arquitectura.md) y [trazabilidad de pruebas](trazabilidad-pruebas.md).

## Registrar cuenta

```mermaid
flowchart LR
    A["Persona<br/>Ingresa código, correo y contraseña"]
    B["Presentación: Registrar<br/>Recoge los datos del formulario"]
    C["Lógica<br/>register_student_account(código, correo, contraseña)<br/>Valida que el código exista, que el usuario esté activo,<br/>que el correo corresponda y que no tenga cuenta"]
    D["Resultado<br/>Si acepta crea la cuenta como Solicitante y dirige al login<br/>Si falla este muestra el motivo del rechazo"]

    A --> B
    B --> C
    C --> D
```

La presentación recoge los datos, la lógica aplica las reglas de registro y la presentación comunica si la cuenta fue creada o rechazada.

## Iniciar sesión

```mermaid
flowchart LR
    A["Persona<br/>Ingresa código y contraseña"]
    B["Presentación: Iniciar sesión<br/>Recoge las credenciales"]
    C["Lógica<br/>authenticate_user(código (identificador), contraseña)<br/>Valida que el usuario este activo, contraseña y rol permitido"]
    D["Resultado<br/>Si acepta entonces inicia sesión y dirige al panel correspondiente que se debe mostrar<br/>Si falla se informa que el código o contraseña estan incorrectos, o cuenta no habilitada"]

    A --> B
    B --> C
    C --> D
```

La presentación recoge las credenciales, la lógica comprueba la cuenta y la presentación comunica el resultado o dirige al usuario a su panel.

## Consultar salas, horarios y reservas propias

```mermaid
flowchart LR
    A["Persona<br/>Solicitante o Administrador<br/>Abre el panel de salas"]
    B["Presentación<br/>panel_solicitante.html<br/>student_panel_view() recibe GET<br/>Solicita el contexto del usuario conectado"]
    C["Lógica<br/>get_student_panel(código)<br/>Consulta salas activas, bloques, reservas propias y avisos<br/>Excluye bloques retirados o finalizados"]
    D["Resultado<br/>Muestra disponibilidad, reservas propias y avisos<br/>El Operante recibe 403 si intenta acceder a este panel"]

    A --> B
    B --> C
    C --> D
```

La consulta no crea reservas. Tener una sanción vigente permite consultar, pero impide crear o modificar reservas.

## Crear una reserva propia

```mermaid
flowchart LR
    A["Persona<br/>Solicitante o Administrador<br/>Selecciona sala, horario y actividad"]
    B["Presentación<br/>panel_solicitante.html<br/>student_panel_view() recibe POST<br/>_intentar_crear_reserva() lee los campos"]
    C["Lógica<br/>create_student_reservation() → create_reservation()<br/>Valida cuenta, calendario, sanciones y disponibilidad<br/>Comprueba ocupación, consecutividad y limpieza"]
    D["Resultado<br/>Si acepta, crea Reserva y Auditoria y vuelve al panel<br/>Si falla, muestra el motivo sin crear la reserva"]

    A --> B
    B --> C
    C --> D
```

Actor y titular son el mismo usuario. El Administrador que reserva para sí mismo está exceptuado de la restricción de mismo horario y bloques consecutivos. La regla de calendario prohíbe reservar sábados, domingos y feriados configurados.

## Modificar una reserva como Solicitante o Administrador

```mermaid
flowchart LR
    A["Persona<br/>Solicitante o Administrador<br/>Elige una reserva y un nuevo bloque"]
    B["Presentación<br/>modificar_reserva.html<br/>modify_reservation_view() prepara destinos con GET<br/>Con POST llama a _intentar_modificar_reserva()"]
    C["Lógica<br/>get_reservation_modification_panel() prepara las opciones<br/>modify_student_reservation() → modify_reservation()<br/>Valida permisos, reserva confirmada y destino diferente"]
    D["Resultado<br/>Si acepta, cambia el bloque y guarda auditoría<br/>Si falla, conserva la reserva original e informa el motivo"]

    A --> B
    B --> C
    C --> D
```

El Solicitante necesita al menos 60 minutos de anticipación. El Administrador omite ese plazo y la restricción de consecutividad, pero respeta disponibilidad, sanciones, mantenimiento y limpieza. Si modifica una reserva ajena, se notifica al titular y vuelve a gestión de reservas; si es propia, vuelve al panel de salas.

## Cancelar una reserva propia

```mermaid
flowchart LR
    A["Persona<br/>Solicitante o Administrador<br/>Confirma cancelar su reserva"]
    B["Presentación<br/>panel_solicitante.html<br/>cancel_reservation_view() recibe POST<br/>El Solicitante ve una advertencia si cancelaría tarde"]
    C["Lógica<br/>cancel_reservation(actor, reserva)<br/>Valida permisos y estado confirmado<br/>Evalúa inicio y rol para decidir la sanción"]
    D["Resultado<br/>Guarda CANCELADA y Auditoria<br/>Devuelve reserva y sanción opcional<br/>Muestra el resultado y vuelve al panel"]

    A --> B
    B --> C
    C --> D
```

El Solicitante solo cancela antes del inicio: con 60 minutos o más no hay sanción; con menos de 60 minutos, _registrar_sancion_por_cancelacion() cuenta las faltas automáticas y aplica 24 horas, 48 horas, 168 horas o semestre. Las duraciones fijas omiten sábados y domingos. El Administrador puede cancelar una reserva propia confirmada incluso iniciada y no recibe sanción automática. Si se rechaza la operación, no cambia la reserva ni aumenta el contador.

## Marcar una notificación como leída

```mermaid
flowchart LR
    A["Persona<br/>Solicitante<br/>Pulsa Entendido en un aviso"]
    B["Presentación<br/>panel_solicitante.html<br/>mark_notification_read_view() recibe POST<br/>Recibe el identificador del aviso"]
    C["Lógica<br/>mark_notification_as_read(código, aviso)<br/>Busca el aviso por ID y destinatario<br/>Actualiza únicamente leida=True"]
    D["Resultado<br/>Conserva el aviso en el historial y vuelve al panel<br/>Si es ajeno o inexistente, muestra rechazo sin modificarlo"]

    A --> B
    B --> C
    C --> D
```

Los avisos persistentes son distintos de los mensajes temporales de éxito o error mostrados al enviar un formulario.

## Buscar un Solicitante desde el panel del Operante

```mermaid
flowchart LR
    A["Persona<br/>Operante<br/>Introduce el código del estudiante"]
    B["Presentación<br/>panel_operante.html<br/>operator_panel_view() recibe GET con acción y código<br/>_construir_contexto_operante() prepara los datos"]
    C["Lógica<br/>_validar_codigo_operante() y get_operator_student()<br/>Exigen código existente, rol Solicitante, cuenta activa y registrada<br/>get_operator_student_summary() y get_operator_availability()"]
    D["Resultado<br/>Muestra estudiante, reservas, sanción y disponibilidad<br/>Si no está registrado, informa que debe crear su cuenta"]

    A --> B
    B --> C
    C --> D
```

Una fila precargada sin contraseña no basta. La comprobación también se aplica en los servicios al crear, modificar o cancelar, aunque se envíe la operación sin usar el buscador.

## Crear una reserva asistida

```mermaid
flowchart LR
    A["Persona<br/>Operante<br/>Selecciona estudiante, bloque y actividad"]
    B["Presentación<br/>panel_operante.html<br/>POST a operator_panel_view() con acción reservar<br/>_procesar_accion_operante() lee los datos"]
    C["Lógica<br/>create_reservation(operante, solicitante, bloque, actividad)<br/>Valida estudiante registrado y reglas del titular<br/>Comprueba sanción, calendario, ocupación y limpieza"]
    D["Resultado<br/>Crea la reserva para el estudiante<br/>Registra al Operante como actor en Auditoria<br/>Vuelve a la sección reservar con el resultado"]

    A --> B
    B --> C
    C --> D
```

El titular y el actor son distintos. El Operante no obtiene la excepción administrativa de consecutividad.

## Modificar una reserva asistida

```mermaid
flowchart LR
    A["Persona<br/>Operante<br/>Elige una reserva del estudiante y otro bloque"]
    B["Presentación<br/>panel_operante.html<br/>POST con acción modificar<br/>_leer_id_reserva_operante() comprueba el titular"]
    C["Lógica<br/>modify_reservation(operante, reserva, destino)<br/>Exige estudiante activo y registrado, reserva confirmada<br/>Al menos 60 minutos y reglas del destino"]
    D["Resultado<br/>Actualiza el bloque, guarda auditoría y notifica al titular<br/>Si falla, conserva la reserva original<br/>Vuelve a la sección modificar"]

    A --> B
    B --> C
    C --> D
```

Para mostrar las opciones se utiliza get_reservation_modification_panel_for_actor(). El Operante tiene permiso para gestionar reservas ajenas, pero no está exceptuado del plazo ni de la consecutividad.

## Cancelar una reserva asistida

```mermaid
flowchart LR
    A["Persona<br/>Operante<br/>Confirma cancelar una reserva del estudiante"]
    B["Presentación<br/>panel_operante.html<br/>POST con acción cancelar<br/>_procesar_accion_operante() comprueba el titular"]
    C["Lógica<br/>cancel_reservation(operante, reserva)<br/>Exige estudiante registrado y reserva confirmada<br/>Rechaza si la reserva ya comenzó"]
    D["Resultado<br/>Cancela, guarda auditoría y notifica al titular<br/>No crea sanción ni suma una falta automática<br/>Vuelve a la sección cancelar"]

    A --> B
    B --> C
    C --> D
```

La ausencia de sanción depende del actor Operante: aunque falten menos de 60 minutos, no se sanciona al titular. Si el plazo de inicio ya pasó, la cancelación se rechaza.

## Consultar reservas desde la gestión administrativa

```mermaid
flowchart LR
    A["Persona<br/>Administrador<br/>Abre Gestionar reservas"]
    B["Presentación<br/>gestion_cancelaciones.html<br/>admin_cancellations_view() recibe GET<br/>Exige rol Administrador"]
    C["Lógica<br/>get_admin_cancellable_reservations(código_admin)<br/>Consulta reservas confirmadas de hoy en adelante<br/>Ordena por fecha y horario"]
    D["Resultado<br/>Muestra la lista con acciones Modificar y Cancelar<br/>Los demás roles no pueden abrir esta gestión"]

    A --> B
    B --> C
    C --> D
```

La modificación administrativa utiliza el recorrido de modify_reservation_view() descrito antes, con las excepciones del Administrador.

## Cancelar una reserva desde la gestión administrativa

```mermaid
flowchart LR
    A["Persona<br/>Administrador<br/>Confirma cancelar una reserva del listado"]
    B["Presentación<br/>gestion_cancelaciones.html<br/>admin_cancel_reservation_view() recibe POST<br/>Recibe el ID de reserva desde la URL"]
    C["Lógica<br/>cancel_reservation(admin, reserva)<br/>Valida cuenta, acceso y reserva confirmada<br/>Omite la restricción por inicio y la sanción automática"]
    D["Resultado<br/>Cancela y registra Auditoria<br/>Notifica si el titular es otra persona<br/>Vuelve a Gestionar reservas"]

    A --> B
    B --> C
    C --> D
```

No aumenta el contador de faltas automáticas. Si la reserva ya está cancelada, afectada por mantenimiento o no existe, se rechaza sin repetir la operación.

## Bloquear un horario por mantenimiento

```mermaid
flowchart LR
    A["Persona<br/>Administrador u Operante<br/>Selecciona sala, horario y motivo"]
    B["Presentación<br/>dashboard.html → block_room_view()<br/>o panel_operante.html → operator_panel_view()<br/>Ambos usan _procesar_bloqueo_mantenimiento()"]
    C["Lógica<br/>block_room_schedule_for_maintenance(actor, bloque, motivo)<br/>Valida permisos, existencia, estado y motivo<br/>Para Operante exige turno de hoy no iniciado"]
    D["Resultado<br/>Guarda MANTENIMIENTO y Bloqueo<br/>Reservas confirmadas pasan a POR_MANTENIMIENTO<br/>Crea auditorías y avisos sin sancionar"]

    A --> B
    B --> C
    C --> D
```

El Administrador puede bloquear incluso un turno iniciado o finalizado. Se afectan las reservas confirmadas de la combinación en todas sus fechas. El Administrador vuelve al dashboard y el Operante a su sección de mantenimiento. Un bloqueo no desaparece al terminar el turno.

## Retirar un bloqueo de mantenimiento

```mermaid
flowchart LR
    A["Persona<br/>Administrador u Operante<br/>Pulsa sacar o quitar mantenimiento"]
    B["Presentación<br/>dashboard.html → unblock_room_view()<br/>o panel_operante.html → operator_unblock_room_view()<br/>El botón envía POST con el ID del bloque"]
    C["Lógica<br/>unblock_room_schedule_from_maintenance(actor, bloque)<br/>Valida permisos y bloqueo activo<br/>can_unblock_maintenance() comprueba el plazo"]
    D["Resultado<br/>Vuelve a DISPONIBLE y guarda Desbloqueo<br/>No restaura reservas afectadas<br/>Si falla, muestra el motivo y conserva el bloqueo"]

    A --> B
    B --> C
    C --> D
```

Ambos roles solo pueden retirar antes del inicio del horario en la fecha original del bloqueo. La redirección vuelve a la pantalla de mantenimiento correspondiente al rol.

## Consultar sanciones

```mermaid
flowchart LR
    A["Persona<br/>Administrador<br/>Busca o filtra Solicitantes"]
    B["Presentación<br/>gestion_sanciones.html<br/>sanctions_admin_view() recibe GET<br/>Lee búsqueda y filtro"]
    C["Lógica<br/>get_solicitantes(término, filtro)<br/>Consulta usuarios y sanciones_vigentes(ahora)<br/>Aplica búsqueda y filtros seleccionados"]
    D["Resultado<br/>Muestra los Solicitantes y su sanción vigente<br/>Permite elegir las acciones de sanción autorizadas"]

    A --> B
    B --> C
    C --> D
```

La consulta es de lectura. La presentación utiliza los datos devueltos para mostrar el motivo, vencimiento y opciones de gestión.

## Aplicar una sanción manual

```mermaid
flowchart LR
    A["Persona<br/>Administrador<br/>Elige estudiante, duración y motivo"]
    B["Presentación<br/>gestion_sanciones.html<br/>apply_sanction_view() recibe POST<br/>Valida el código del formulario"]
    C["Lógica<br/>apply_manual_sanction(admin, solicitante, duración, motivo)<br/>Valida Administrador, estudiante, duración y motivo<br/>Retira la vigente y calcula el nuevo vencimiento"]
    D["Resultado<br/>Crea Sancion MANUAL con responsable<br/>Muestra el vencimiento y vuelve a Sanciones<br/>Si falla, informa el rechazo sin cambios parciales"]

    A --> B
    B --> C
    C --> D
```

Las duraciones fijas omiten sábados y domingos; semestre vence el próximo 1 de enero o julio. La sanción manual no suma faltas automáticas ni crea un aviso persistente para el estudiante. Al intentar crear o modificar una reserva, este recibe un mensaje con motivo y fecha y hora de vencimiento en La Paz.

## Retirar una sanción individual

```mermaid
flowchart LR
    A["Persona<br/>Administrador<br/>Confirma retirar una sanción vigente"]
    B["Presentación<br/>gestion_sanciones.html<br/>withdraw_sanction_view() recibe POST<br/>Recibe el ID de la sanción"]
    C["Lógica<br/>withdraw_sanction(admin, sanción)<br/>Exige Administrador activo y sanción vigente<br/>Guarda fecha_retiro y retirada_por"]
    D["Resultado<br/>La sanción deja de bloquear y se conserva el registro<br/>No reinicia el contador de faltas<br/>Vuelve a Sanciones con el resultado"]

    A --> B
    B --> C
    C --> D
```

La fecha de fin original no se sobrescribe. Un segundo retiro o una sanción inexistente o no vigente se rechaza.

## Reiniciar sanciones y contadores

```mermaid
flowchart LR
    A["Persona<br/>Administrador<br/>Confirma el reinicio general manual"]
    B["Presentación<br/>gestion_sanciones.html<br/>clear_sanctions_view() recibe POST<br/>Exige rol Administrador"]
    C["Lógica<br/>clear_all_sanctions(admin)<br/>Crea ReinicioSanciones y retira todas las vigentes<br/>Usa el mismo instante y responsable para los retiros"]
    D["Resultado<br/>Los contadores quedan en cero y cesan los bloqueos vigentes<br/>Conserva historial y fechas originales<br/>Informa cuántas sanciones retiró y vuelve a Sanciones"]

    A --> B
    B --> C
    C --> D
```

La misma fecha y hora se guarda en ReinicioSanciones.fecha y fecha_retiro de las sanciones manuales y automáticas vigentes. contar_faltas() considera solo faltas automáticas posteriores al corte. El cambio semestral automático se calcula por fechas y no es una acción iniciada desde esta pantalla.

## Cerrar sesión

```mermaid
flowchart LR
    A["Persona<br/>Usuario autenticado<br/>Pulsa Salir"]
    B["Presentación<br/>Enlace de salida de la interfaz<br/>logout_view() recibe la solicitud"]
    C["Lógica<br/>request.session.flush()<br/>Elimina los datos de la sesión actual"]
    D["Resultado<br/>Muestra el mensaje de cierre y redirige al login<br/>Para volver a las pantallas protegidas debe autenticarse"]

    A --> B
    B --> C
    C --> D
```

El cierre de sesión no elimina la cuenta ni las reservas del usuario.
