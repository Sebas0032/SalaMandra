# Sesiones 8 y 9 — Plan del incremento: Bloqueo de salas por Mantenimiento

- Proyecto: SalaMandra — Reserva de Salas de Estudio
- Integrantes: Luciana Soza (@luci-solar34), Sebastian Cruz (@Sebas0032), Sebastian Soto (@sebas-sst)
- Fecha de planificación: 06 de octubre de 2026
- Fuentes: [`docs/sesion-06-requisitos.md`](sesion-06-requisitos.md) (RES-RF-03), [`docs/sesion-07-modelos.md`](sesion-07-modelos.md) (RES-HU-02, RES-CU-02, RES-MOD-02)
- Flujo elegido: **Bloqueo de sala por Mantenimiento y cancelación automática de reservas**
- IDs de requisitos: **RES-RF-03**

---

## 1. Alcance del incremento

### Incluye:
- Implementación de los estados `EN_MANTENIMIENTO` y `POR_MANTENIMIENTO` en los modelos de Django para Sala y Reserva
- Lógica de autorización: solo usuarios con rol Administrador pueden bloquear salas
- Función `block_room_for_maintenance()` que:
  - Valida permisos del usuario
  - Verifica que la sala exista
  - Busca todas las reservas confirmadas en esa sala
  - Cambia estado de reservas a `POR_MANTENIMIENTO` **sin aplicar penalizaciones**
  - Cambia estado de la sala a `EN_MANTENIMIENTO`
  - Registra el motivo del bloqueo
- Casos de aceptación: bloqueo exitoso de una sala con la reserva confirmada
- Casos de rechazo: usuario sin permisos, sala no existe
- Pruebas unitarias con pytest/Django Test Runner
- Demostración funcional o ejemplo de uso

### Excluye (futura iteración):
- Notificación automática a estudiantes (pendiente de aclaración con Sergio)
- Desbloqueo manual de salas
- Historial detallado de bloqueos

### Supuestos:
- La base de datos ya realizada y planteada
- Existe un modelo `Room` con estado y un modelo `Reservation` con estado
- Existe modelo de autorización para usuarios con rol Administrador
- Las reservas activas/confirmadas ya existen en la BD con estado `CONFIRMADA`

### Dependencias técnicas externas:
- Modelo de usuarios con roles 

---

## 2. Cuatro tareas del incremento

| Tarea | Descripción | Esfuerzo (h-p) | Duración (días) | Predecesoras | Responsable | Evidencia de cierre |
|---|---|---|---|---|---|---|
| **T1: Realizar modelos de Django** | Agregar estado EN_MANTENIMIENTO y POR_MANTENIMIENTO a Room y Reservation. Crear migraciones. | 3 | 1 | — | Sebastian Cruz | Migraciones por ejecutar sin errores, modelos comprobados en Django shell |
| **T2: Implementar función de negocio** | Codificar `block_room_for_maintenance(user, room_id, reason)` en `services.py`. Incluir validaciones de autorización, existencia de sala, búsqueda y cambio de estado de reservas. | 4 | 1 | T1 | Sebastian Soto | Función por implementar, pruebas manuales en consola Django |
| **T3: Escribir pruebas automatizadas** | Test unitario: bloqueo exitoso (pasa a POR_MANTENIMIENTO). Test de rechazo: usuario sin permisos (rechaza, no cambia). Test límite: sala sin reservas (bloquea, estado actualizado). | 3 | 1 | T2 | Luciana Soza | Archivo `test_maintenance_block.py` con 4 casos, cobertura por verificar, tests ejecutados |
| **T4: Demostración** | Hacer demostración con datos . Actualizar README o docs con ejemplo de uso. | 2.5 | 1 | T3 | [Rotativa] | ejemplo ejecutable sin errores, documentación actualizada en repo |

**Notas de estimación:**
- **T1 (3 h-p, 1 día):** Modelos simples, sin lógica compleja. Cabe en 1 día de trabajo concentrado (8h). 
- **T2 (4 h-p, 1 día):** Lógica de autorización + búsqueda + actualización. Complejidad media, pero concentrable en 1 día con foco. Referencia: función `create_reservation()` existente.
- **T3 (3 h-p, 1 día):** 4 tests (caso aceptado, 2 rechazos, límite). Ejecutable en 1 día con tests de PyTest.
- **T4 (2.5 h-p, 1 día):** Documentación integrada. Cabe en 1 día.

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
T3 (Duración: 1 día) ← Escribir tests
  |
  v
T4 (Duración: 1 día) ← demostración
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

**Meta final:** 4 días

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
Semana 1 (Lunes–Jueves = 4 días de trabajo)
══════════════════════════════════════════════════════════════

Martes        │ Miercoles     │ Jueves        │ Viernes
──────────────┼───────────────┼───────────────┼──────────────

T1 Modelos    │ T2 Función    │ T3 Tests      │ T4 Demo
[████████████]│[███████████████][███████████] │[██████████████]

Día 1         │ Día 2         │ Día 3         │ Día 4
```

**Duración total:** 4 días consecutivos de trabajo (1 día por tarea, secuencial).

---

## 4. Comprobación de disponibilidad

### Supuesto de disponibilidad del equipo:

Asumiendo que cuentan con **4 días de trabajo concentrado** (Martes-Viernes):

| Persona | Disponible | Tareas asignadas | Esfuerzo requerido (h-p) | ¿Puede hacerlo? |
|---|---|---|---|---|
| Luciana Soza | 4 días (32h) | T3 (2.5 h-p, rol: escritura de tests, 1 día) | 2.5 h-p |  Sí |
| Sebastian Cruz | 4 días (32h) | T1 (3 h-p, rol: modelos, 1 día) | 3 h-p |  Sí |
| Sebastian Soto | 4 días (32h) | T2 (4 h-p, rol: lógica principal, 1 día) + T4 (2.5 h-p, 1 día) | 6.5 h-p | Sí |

**Total de esfuerzo-persona necesario: 12.5 h-p**
**Total de disponibilidad (3 personas × 32h/persona): 96 h-p**

**Conclusión:** La disponibilidad es **ampliamente suficiente**. Cada persona necesita menos de 7 h-p de un total de 32h disponibles. La secuencialidad de tareas (4 días) cabe perfectamente en la semana de trabajo.

### Potencial conflicto (si ocurre):

Si una tarea se demora más de 1 día (ej: T2 toma 1.5 días), se desplaza todo lo posterior. **Solución:** Aumentar paralelismo donde sea posible (ej: Luciana comienza a escribir templates de tests mientras Sebastian termina la función, preparando el código para T3).

---

## 5. Dos riesgos

| Riesgo | Probabilidad y razón | Consecuencia en el incremento | Respuesta antes del problema | Señal y contingencia | Responsable |
|---|---|---|---|---|---|
| **R1: Modelo de usuarios/roles no definido o incompleto** | **Media** — Aun está pendiente cómo se almacenan y validan los roles de Administrador en Django. | T1 podría no poder crear la validación; T2 se bloquea esperando un patrón de autorización. Duración de T1 puede pasar de 2h a 3.5h; cascada a T2 y T3. | Sesión 6–7: aclarar con Sergio cómo se modelan usuarios/roles. Si no está listo, T1 puede crear un stub (ej: `is_maintenance` bool) para avanzar. Revisar `proyecto/estudiante.py` y confirmar si existe modelo de User. | Si T1 se demora >30min sin claridad, activar OP-01: pausa de 1h con Sergio para definir roles. | Sebastian Cruz |
| **R2: Cambio de estado de 3+ reservas sin errores de concurrencia** | **Baja-Media** — Si dos usuarios llaman a `block_room_for_maintenance()` simultáneamente, la BD podría actualizar reservas dos veces. En equipo pequeño y pruebas locales, probabilidad **baja**; si se integra con servidor, sube a **media**. | T2/T3 no validan transacciones; pruebas falsamente positivas. En producción, perderían garantía de "una sola cancelación por reserva". Duración de T3 +1h para agregar transacciones y test de concurrencia. | T2: usar `@transaction.atomic()` en `block_room_for_maintenance()` desde el inicio. T3: agregar test de concurrencia simulado (ej: dos llamadas en paralelo, comprobar que solo una gana). | Si el primer test de concurrencia falla, pausa de 30min. Si la BD local carece de capacidad de transacciones, usar SQLite en modo WAL y documentar limitación. | Sebastian Soto |

---

## 6. Entregable, hito y evidencia

### Entregable:
1. **Código implementado** (`proyecto/models.py` o módulo equivalente, `services.py`)
2. **Suite de pruebas** (`tests/test_maintenance_block.py`)
3. **Documentación de uso** (endpoint REST o comando CLI con ejemplo)
4. **Commit en rama o PR en GitHub** con mensaje que referencia RES-RF-03 de sesión 6
5. **Estado verificable** en GitHub (rama actualizada, tests ejecutándose en CI si aplica)

### Hito verificable: "RES-RF-03 implementado y comprobado"

**Criterios de aceptación:**
-  **Caso aceptado:** Usuario con rol Mantenimiento bloquea Sala B-102 que tiene 2 reservas confirmadas.
  - Sala pasa a estado `EN_MANTENIMIENTO`
  - Ambas reservas pasan a estado `POR_MANTENIMIENTO`
  - No se registran penalizaciones en el historial de estudiantes
  - Se registra el motivo del bloqueo en la BD
  - Sistema responde en < 2 segundos
- **Caso de rechazo 1:** Usuario **sin** rol Administrador intenta bloquear.
- Sistema rechaza con mensaje "No tienes permisos para bloquear salas"
  - Sala y reservas no cambian de estado
-  **Caso de rechazo 2:** Usuario intenta bloquear Sala X (no existe).
  - Sistema rechaza con mensaje "La sala X no existe"
  - No se modifica nada en la BD
-  **Caso límite:** Sala sin reservas se bloquea exitosamente.
  - Sala pasa a `EN_MANTENIMIENTO`
  - Sistema no lanza excepción
-  **Pruebas:** la función `block_room_for_maintenance()` hace su trabajo y sus validaciones
-  **Documentación:** README actualizado con ejemplo ejecutable

**No es suficiente:**
-  Código que compila pero tests no pasan
-  Tests que pasan pero funcionalidad no demostrare en vivo
-  Documentación incompleta sin ejemplo de uso

### Estado real del trabajo (al cerrar esta actividad — sesión 08-09)

| Tarea | Estado | Evidencia o explicación |
|---|---|---|
| T1 | **No iniciada** | Se inicia hoy. Modelo y migraciones pendientes de implementar. |
| T2 | **No iniciada** | Depende de T1. Función `block_room_for_maintenance()` aún no codificada. |
| T3 | **No iniciada** | Depende de T2. Archivo `test_maintenance_block.py` no existe. |
| T4 | **No iniciada** | Depende de T3. Documentación no integrados. |

**Horas reales registradas:** No registradas (planificación solo; implementación comienza después).

---

## 7. Siguiente paso y revisión

### Siguiente acción:
1. **Revisar con Sergio:** Aclarar modelo de usuarios y roles antes de iniciar T1 (OP-01 si es necesario).
2. **Iniciar T1 esta semana:** Crear/actualizar modelos de Room, Reservation, Maintenance en Django.
3. **Hito intermedio:** Migraciones ejecutadas correctamente, modelos verificados.
4. **Revisión en sesión 10:** Presentar incremento terminado con pruebas y demostración.

### Condición que obliga a revisar el plan:

-  Si el modelo de usuarios/roles **no existe y no está aprobado por Sergio**, parar T1 y escalar.
-  Si T1 se demora > 3.5 horas (en lugar de 2), revisar holgura en T2/T3/T4.
-  Si en T3 descubren que la función de T2 tiene diseño defectuoso, retroceder y corregir (T2 → T3 no puede avanzar).
-  Si Sergio cambia los requisitos de bloqueo (ej: agregar notificaciones automáticas), actualizar alcance y replanificar.

---

## 8. Coherencia final

### Checklist de revisión antes de entregar

- [x] El incremento continúa requisitos RES-RF-03 (sesión 6) y modelos RES-CU-02/MOD-02 (sesión 7)
- [x] Alcance es pequeño y con sentido (un flujo, caso aceptado + rechazo)
- [x] Las 4 tareas tienen esfuerzo, duración, responsables y evidencia concreta
- [x] Red CPM es acíclica y el cálculo de tiempos es correcto
- [x] Ruta crítica está identificada (holgura 0 en todas las tareas)
- [x] Gantt visual es coherente con la secuencia
- [x] Disponibilidad: 12.5 h-p requeridas vs 30 h-p disponibles 
- [x] Se definen 2 riesgos concretos con probabilidad, consecuencia y respuesta
- [x] Hito verificable y criterios de aceptación explícitos
- [x] Estado real: tareas no iniciadas, horas no registradas
- [x] Siguiente paso tiene responsable y momento de revisión

---

## Participación y notas

- **Luciana Soza:** Responsable de T3 (tests); revisión de coherencia global.
- **Sebastian Cruz:** Responsable de T1 (modelos); coordinación de dependencias con T2.
- **Sebastian Soto:** Responsable de T2 (lógica) y co-responsable de T4 (integración).

**Asistencia de IA:**
- Herramienta: Claude (asistente IA)
- Propósito: Estructura del archivo, tabla de tareas, cálculos CPM y Gantt
- Aporte: Template de plan, ejemplos de estimación y formato de riesgos
- Verificación: El equipo adaptó IDs, duraciones y responsables a SalaMandra; confirmaron que T1→T2→T3→T4 es la secuencia correcta

---
