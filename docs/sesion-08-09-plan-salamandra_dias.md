# Sesiones 8 y 9 — Plan del incremento: Bloqueo de horarios de sala por Mantenimiento

- Proyecto: SalaMandra — Reserva de Salas de Estudio
- Integrantes: Luciana Soza (@luci-solar34), Sebastian Cruz (@Sebas0032), Sebastian Soto (@sebas-sst)
- Fecha de planificación: 06 de octubre de 2026
- Fuentes: [`docs/sesion-06-requisitos.md`](sesion-06-requisitos.md) (RES-RF-03), [`docs/sesion-07-modelos.md`](sesion-07-modelos.md) (RES-HU-02, RES-CU-02, RES-MOD-02)
- Flujo elegido: **Bloqueo de un horario específico de una sala por Mantenimiento y cambio automático de la reserva asociada**
- IDs de requisitos: **RES-RF-03**

---

## 1. Alcance del incremento

### Incluye:
- Implementación del estado `MANTENIMIENTO` para `Sala_Horario` y del estado `POR_MANTENIMIENTO` para `Reserva`
- Lógica de autorización: solo usuarios con rol Administrador pueden bloquear un horario específico de una sala
- Función `block_sala_horario_for_maintenance()` que:
  - Valida los permisos del usuario
  - Verifica que la sala y el horario seleccionado existan
  - Verifica que el `Sala_Horario` no esté ya en estado `MANTENIMIENTO`
  - Busca la reserva confirmada asociada al horario seleccionado
  - Cambia la reserva a `POR_MANTENIMIENTO` **sin aplicar penalizaciones**
  - Cambia el estado del `Sala_Horario` a `MANTENIMIENTO`
  - Registra el motivo y la fecha del bloqueo
- Caso de aceptación: bloqueo exitoso de un horario específico de una sala con una reserva confirmada
- Casos de rechazo: usuario sin permisos, sala no existe o el horario ya está bloqueado
- Pruebas unitarias con pytest/Django Test Runner
- Demostración funcional o ejemplo de uso

### Excluye (futura iteración):
- Notificación automática a estudiantes (pendiente de aclaración con Sergio)
- Liberación o desbloqueo del horario de la sala (pendiente de aclaración con Sergio)

### Supuestos:
- La estructura de base de datos y las relaciones entre Sala, Sala_Horario y Reserva ya están planteadas
- Existe un modelo `Sala_Horario` relacionado con una sala y con las reservas correspondientes
- Existe un modelo de autorización para usuarios con rol Administrador
- Las reservas confirmadas ya existen en la BD con estado `CONFIRMADA`
- El bloqueo afecta únicamente al horario seleccionado; los demás horarios de la misma sala permanecen disponibles
- Si el horario seleccionado no tiene una reserva confirmada, el bloqueo se realiza igualmente

### Dependencias técnicas externas:
- Modelo de usuarios con roles
- Relaciones existentes entre `Sala`, `Sala_Horario` y `Reserva`
- Persistencia mediante Django 

---

## 2. Cuatro tareas del incremento

| Tarea | Descripción | Esfuerzo (h-p) | Duración (días) | Predecesoras | Responsable | Evidencia de cierre |
|---|---|---|---|---|---|---|
| **T1: Agregar modelos de Django** | Agregar el estado `MANTENIMIENTO` a `Sala_Horario` y `POR_MANTENIMIENTO` a `Reservas`. Crear las migraciones necesarias. | 3 | 1 | — | Sebastian Cruz | Migraciones ejecutadas sin errores y modelos comprobados en Django shell |
| **T2: Implementar función de negocio** | Codificar `block_sala_horario_for_maintenance(user, sala_horario_id, reason)` en `services.py`. Incluir validación de autorización, existencia del horario, bloqueo y actualización de la reserva asociada. | 4 | 1 | T1 | Sebastian Soto | Función implementada y prueba manual del flujo en Django |
| **T3: Escribir pruebas automatizadas** | Crear pruebas para bloqueo exitoso, usuario sin permisos, sala inexistente y bloqueo de un horario sin reserva confirmada. | 3 | 1 | T2 | Luciana Soza | Archivo de pruebas creado y pruebas ejecutadas correctamente |
| **T4: Demostración y documentación** | Realizar la demostración del flujo y actualizar la documentación con un ejemplo de uso. | 2.5 | 1 | T3 | Sebastian Soto | Demostración realizada y documentación actualizada en el repositorio |

**Notas de estimación:**
- **T1 (3 h-p, 1 día):** Agregar modelos y migraciones. Es una tarea acotada y puede realizarse durante un día de trabajo.
- **T2 (4 h-p, 1 día):** Implementación de la lógica de autorización, validación y actualización del `Sala_Horario` y su reserva asociada.
- **T3 (3 h-p, 1 día):** Elaboración y ejecución de las pruebas correspondientes al flujo y sus casos de rechazo.
- **T4 (2.5 h-p, 1 día):** Demostración del flujo y actualización de la documentación.

**Total de esfuerzo: 12.5 h-p**
**Duración total: 4 días** (T1 + T2 + T3 + T4 secuenciales)

---

## 3. Red de dependencias, cálculos CPM y Gantt

### Diagrama de dependencias (texto plano CPM)

```
Inicio
  |
  v
T1 (Duración: 1 día) ← Actualizar modelos
  |
  v
T2 (Duración: 1 día) ← Implementar función
  |
  v
T3 (Duración: 1 día) ← Escribir pruebas
  |
  v
T4 (Duración: 1 día) ← Demostración y documentación
  |
  v
Fin
```

**Observación:** Las tareas son **secuenciales** (T1 → T2 → T3 → T4). No hay paralelismo posible porque T2 requiere los modelos de T1, T3 requiere el código de T2, y T4 requiere la cobertura de pruebas de T3.

### Cálculos de tiempos tempranos (Forward Pass)

| Tarea | IT (Inicio Temprano, días) | FT (Fin Temprano, días) |
|---|---|---|
| T1 | 0 | 0 + 1 = **1** |
| T2 | 1 | 1 + 1 = **2** |
| T3 | 2 | 2 + 1 = **3** |
| T4 | 3 | 3 + 1 = **4** |

**Inicio del incremento:** martes.
**Meta final:** viernes, después de completar T4.
**Duración total:** 4 días.

### Cálculos de tiempos tardíos (Backward Pass)

| Tarea | FTa (Fin Tardío, días) | ITa (Inicio Tardío, días) | Holgura (días) |
|---|---|---|---|
| T4 | 4 | 4 − 1 = **3** | **0** |
| T3 | 3 | 3 − 1 = **2** | **0** |
| T2 | 2 | 2 − 1 = **1** | **0** |
| T1 | 1 | 1 − 1 = **0** | **0** |

**Ruta crítica:** T1 → T2 → T3 → T4 (todas las tareas tienen holgura **0**, es decir, cualquier demora las retrasa todas).

### Gantt sencillo (representación en texto)

```
Semana 1 (Martes–Viernes = 4 días de trabajo)
══════════════════════════════════════════════════════════════

Martes        │ Miercoles     │ Jueves        │ Viernes
──────────────┼───────────────┼───────────────┼──────────────

T1 Modelos    │ T2 Función    │ T3 Tests      │ T4 Demo
[████████████]│[███████████████][███████████] │[██████████████]

Día 1         │ Día 2         │ Día 3         │ Día 4
```

**Duración total:** 4 días consecutivos de trabajo (1 día por tarea).

---

## 4. Comprobación de disponibilidad

### Supuesto de disponibilidad del equipo:

Se considera que el equipo cuenta con disponibilidad durante los **4 días de trabajo del incremento, de martes a viernes**.

| Persona | Disponible | Tareas asignadas | Esfuerzo requerido (h-p) | ¿Puede hacerlo? |
|---|---|---|---|---|
| Luciana Soza | Martes–viernes | T3 (tests) | 3 h-p | Sí |
| Sebastian Cruz | Martes–viernes | T1 (modelos) | 3 h-p | Sí |
| Sebastian Soto | Martes–viernes | T2 (función) + T4 (demostración) | 6.5 h-p | Sí |

**Total de esfuerzo-persona necesario: 12.5 h-p**
**Total de disponibilidad: 96 h-p (3 personas × 32 h por persona)**

**Conclusión:** La disponibilidad del equipo es suficiente para ejecutar las cuatro tareas durante los cuatro días planificados. No existe conflicto de recursos porque las tareas se realizan de forma secuencial y cada integrante tiene asignada una tarea en el momento correspondiente.

### Gestión ante retrasos:
Si una tarea se demora más de 1 día, se desplazan las tareas posteriores debido a que la ruta crítica es completamente secuencial. En ese caso, se revisará el calendario del incremento y se ajustarán las fechas de las tareas afectadas.

---

## 5. Dos riesgos

| Riesgo | Probabilidad y razón | Consecuencia en el incremento | Respuesta antes del problema | Señal y contingencia | Responsable |
|---|---|---|---|---|---|
| **R1: Ambigüedad sobre el rol autorizado y el estado de la reserva** | **Media** — En los requisitos anteriores aparecen diferencias entre el rol Administrador/Mantenimiento y entre los nombres de estado utilizados para la reserva. | Puede provocar cambios en los modelos y retrasar T1 y T2. | Consultar con Sergio antes de finalizar los modelos y conservar el ID `RES-RF-03`. Registrar la decisión adoptada. | Si no existe una definición confirmada antes de terminar T1, revisar el modelo y el calendario de T2. | Sebastian Cruz |
| **R2: Cambio incorrecto de estados durante el bloqueo** | **Media** — El bloqueo debe actualizar correctamente el `Sala_Horario` y, cuando corresponda, la reserva asociada. | Una actualización incompleta podría dejar el horario bloqueado pero la reserva sin cambiar, o modificar una reserva que no corresponde. | Implementar el flujo de forma controlada y cubrir los estados esperados mediante las pruebas de T3. | Si una prueba detecta que el `Sala_Horario` y la reserva quedan en estados inconsistentes, detener T4 y corregir T2. | Sebastian Soto |

---

## 6. Entregable, hito y evidencia

### Entregable:
1. **Código implementado** para el bloqueo de un `Sala_Horario` por Mantenimiento.
2. **Suite de pruebas automatizadas** que compruebe el flujo y sus casos de rechazo.
3. **Documentación de uso** del flujo implementado.
4. **Commit en GitHub** que relacione la implementación con `RES-RF-03`.

### Hito verificable: "Bloqueo de un horario de sala por Mantenimiento implementado y comprobado"

El hito se considera cumplido cuando se pueda comprobar que:

- Un usuario con rol Administrador selecciona una sala y un horario específico.
- El `Sala_Horario` seleccionado pasa a estado `MANTENIMIENTO`.
- Si existe una reserva confirmada asociada a ese horario, pasa a `POR_MANTENIMIENTO`.
- La reserva no genera penalización al estudiante.
- Se registra el motivo del bloqueo.
- Los demás horarios de la misma sala no son modificados.
- Los casos de rechazo definidos en la Sesión 7 no producen cambios en el sistema.

### Criterios de aceptación:

- **Caso aceptado:** Administrador bloquea un horario específico de una sala que tiene una reserva confirmada.
  - El `Sala_Horario` pasa a `MANTENIMIENTO`.
  - La reserva asociada pasa a `POR_MANTENIMIENTO`.
  - No se aplica penalización.
  - Se registra el motivo y la fecha del bloqueo.
  - Los demás horarios de la sala permanecen sin cambios.

- **Caso de rechazo 1:** Usuario sin rol Administrador intenta bloquear un horario.
  - El sistema rechaza la operación.
  - El `Sala_Horario` y la reserva permanecen sin cambios.

- **Caso de rechazo 2:** Se intenta bloquear un horario perteneciente a una sala que no existe.
  - El sistema rechaza la operación.
  - No se modifica ningún estado.

- **Caso sin reserva confirmada:** Se bloquea un horario que no tiene una reserva confirmada.
  - El `Sala_Horario` pasa a `MANTENIMIENTO`.
  - No se modifica ninguna reserva.

- **Pruebas:** Las pruebas automatizadas comprueban los casos definidos.

- **Documentación:** El repositorio contiene un ejemplo claro del flujo implementado.

### No es suficiente:

- Código que compile pero no tenga pruebas ejecutadas.
- Pruebas que pasen sin comprobar el cambio correcto de estados.
- Documentación que no corresponda al flujo implementado.

### Estado real del trabajo (al cerrar esta actividad — sesión 08-09)

| Tarea | Estado | Evidencia o explicación |
|---|---|---|
| T1 | **No iniciada** | Los cambios en los modelos y las migraciones todavía no fueron implementados. |
| T2 | **No iniciada** | La función `block_sala_horario_for_maintenance()` todavía no fue implementada. |
| T3 | **No iniciada** | Las pruebas automatizadas todavía no fueron creadas ni ejecutadas. |
| T4 | **No iniciada** | La demostración y la documentación todavía no fueron realizadas. |

**Horas reales registradas:** No registradas (planificación solo; implementación comienza después).

---

## 7. Siguiente paso y revisión

### Siguiente acción:
1. **Revisar con Sergio:** aclarar las diferencias identificadas en los requisitos anteriores sobre el rol autorizado y el estado de la reserva, antes de finalizar T1.
2. **Iniciar T1 el martes:** crear y definir los modelos de `Sala_Horario` y `Reservas` y crear las migraciones necesarias.
3. **Hito intermedio:** ejecutar correctamente las migraciones y verificar los estados de los modelos.
4. **Continuar con T2, T3 y T4:** implementar la función, ejecutar las pruebas y realizar la demostración.
5. **Revisión en sesión 10:** presentar el incremento implementado, probado y documentado.

### Condición que obliga a revisar el plan:

- Si Sergio define un rol autorizado diferente al considerado en el plan, actualizar T1 y T2 antes de continuar.
- Si se modifica el nombre o comportamiento de los estados `MANTENIMIENTO` o `POR_MANTENIMIENTO`, actualizar los modelos, pruebas y criterios de aceptación.
- Si durante T1 se detecta que la estructura necesaria para `Sala_Horario` y `Reserva` requiere decisiones adicionales, revisar las estimaciones de T1 y T2.
- Si durante T3 se detecta que el comportamiento implementado en T2 no coincide con los casos definidos en la Sesión 7, detener T4 y corregir T2.
- Si Sergio confirma nuevos requisitos, como notificaciones automáticas o una regla de liberación del horario, actualizar el alcance y replanificar el incremento.

---

## 8. Coherencia final

### Checklist de revisión antes de entregar

- [x] El incremento continúa el requisito `RES-RF-03` de la sesión 6 y los modelos `RES-CU-02` / `RES-MOD-02` de la sesión 7.
- [x] El alcance se centra en el bloqueo de un `Sala_Horario` específico por Mantenimiento.
- [x] Las 4 tareas tienen esfuerzo, duración, responsables, predecesoras y evidencia de cierre.
- [x] La red CPM es acíclica y corresponde a la secuencia T1 → T2 → T3 → T4.
- [x] La ruta crítica está identificada y todas las tareas tienen holgura 0.
- [x] El Gantt es coherente con el inicio el martes y la finalización el viernes.
- [x] La disponibilidad del equipo es suficiente: 12.5 h-p requeridas frente a 96 h-p disponibles.
- [x] Se identifican 2 riesgos con probabilidad, consecuencia, respuesta, señal y responsable.
- [x] Se define un entregable y un hito verificable.
- [x] El estado real refleja que las tareas todavía no fueron iniciadas.
- [x] Se define el siguiente paso y las condiciones que obligarían a revisar el plan.

---

## Participación y notas

- **Luciana Soza:** Responsable de T3 (pruebas); revisión de coherencia global.
- **Sebastian Cruz:** Responsable de T1 (modelos).
- **Sebastian Soto:** Responsable de T2 (lógica) y T4 (demostración y documentación).

**Asistencia de IA:**
- Herramienta: Claude (asistente IA)
- Propósito: Estructura del archivo, tabla de tareas, cálculos CPM y Gantt
- Aporte: Template de plan, ejemplos de estimación y formato de riesgos
- Verificación: Se adaptó IDs, duraciones y responsables.

---
