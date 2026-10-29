# SalaMandra — Reserva de Salas de Estudio

Proyecto de Ingeniería de Software (P02 — Reservas de espacios), adaptado a
un sistema de reserva de salas de estudio universitarias.

## Integrantes
| Integrante | GitHub |
|---|---|
| Luciana Soza | @luci-solar34 |
| Sebastian Cruz | @Sebas0032 |
| Sebastian Toledo | @sebas-sst |

## Estado actual

Este repo contiene **dos partes independientes**:

1. **`proyecto/` + `tests/`**: reglas de negocio puras en Python (Sesiones
   04–06), sin interfaz ni base de datos. Se comprueban con pytest.
2. **`salamandra_project/` + `reservas/`**: la interfaz web (Django +
   **SQLite**) que implementa el **único caso de uso de la Sesión 07**
   (`docs/sesion-07-modelos.md`, RES-CU-02): un **Administrador** inicia
   sesión y **bloquea el horario de una sala por mantenimiento**; las
   reservas confirmadas de ese horario pasan a `POR_MANTENIMIENTO` sin
   penalizar al estudiante.

> **Alcance:** llega hasta la Sesión 07. El plan de las Sesiones 08–09
> (`docs/sesion-08-09-plan-salamandra_dias.md`) queda para la siguiente
> iteración y no está implementado a propósito.

### Base de datos

Se usa **SQLite** con el **ORM de Django**: no hay que instalar ningún
servicio ni configurar usuario o contraseña. Todo se guarda en un archivo,
`db.sqlite3`, que Django crea solo en la raíz del proyecto.

Los modelos (`reservas/models.py`) reproducen el diagrama entidad-relación
del equipo: `roles`, `usuarios`, `usuarios_roles`, `tipo_sancion`,
`sanciones`, `horarios`, `salas`, `sala_horario`, `reservas`, `bloqueos`,
con los mismos nombres de tabla y de columna.

Dos aclaraciones sobre el esquema:

- **`usuarios.password_hash`** no estaba en el diagrama original; se agregó
  porque el login necesita guardar la contraseña.
- En el DDL original, algunas `FOREIGN KEY` de `sala_horario`, `reservas` y
  `bloqueos` apuntaban a la columna equivocada. Se implementó la relación
  lógica correcta (`id_sala → salas.id_salas`, `id_horario →
  horarios.id_horario`, `id_sala_horario → sala_horario.id_sala_horario`).

Solo están instaladas las apps de Django necesarias, así que la base de datos
contiene únicamente las tablas del equipo (más `django_migrations`).

---

## 1. Qué necesitas instalar

| Herramienta | Para qué | Versión |
|---|---|---|
| **Python** | Ejecutar Django (SQLite ya viene incluido con Python) | 3.12 o superior (probado con 3.14) |
| **git** | Clonar/subir el repo | cualquiera reciente |

Nada más. Django se instala con `pip` en el paso 2.

## 2. Preparar el entorno

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
python -m pip install -r requirements.txt
```

Instala `django` y `pytest`.

## 3. Crear las tablas

```bash
python manage.py makemigrations reservas
python manage.py migrate
```

- `makemigrations` genera `reservas/migrations/0001_initial.py` a partir de
  `models.py`. **Haz commit de ese archivo** para que todo el equipo cree
  las mismas tablas.
- `migrate` crea el archivo `db.sqlite3` con todas las tablas.

Las fechas con hora se guardan en SQLite con la hora de `America/La_Paz`
(GMT-4); los horarios de clase y las fechas de reserva ya son datos locales.
Si conservas un `db.sqlite3` creado antes de este cambio, **una sola vez** y
antes de levantar el servidor ejecuta:

```bash
python manage.py convert_legacy_utc --apply
```

El comando crea primero una copia en `.backups/` y convierte las fechas UTC
existentes sin perder segundos ni microsegundos. No se usa en bases nuevas.
SQLite mantiene `CURRENT_TIMESTAMP` en UTC para SQL escrito directamente en
DB Browser. Si insertas fechas a mano, usa `datetime('now', '-4 hours')` para
guardarlas en GMT-4; las escrituras hechas mediante el ORM ya usan La Paz.

## 4. Cargar datos de ejemplo

```bash
python manage.py seed_data
```

Crea (sin duplicar si lo corres de nuevo):

- Roles `Administrador`, `Operante` y `Solicitante` (uno por usuario)
- **Administrador: `admin@salamandra.upb.edu` / `admin123`**
- 16 alumnos con sus códigos y correos de ejemplo, aún sin contraseña; pueden
  crear su cuenta con el código y correo correspondientes. Las reservas de
  ejemplo están a nombre de Luciana Soledad (código 95429)
- Catálogo `tipo_sancion` para sanciones automáticas y manuales
- 6 salas (A, B, C, D, E y F), 6 horarios (`07:45-09:45`, `10:00-12:00`,
  `12:15-14:15`, `14:30-16:30`, `16:45-18:45` y `19:00-21:00`) y las 36
  combinaciones en `sala_horario`
- 2 reservas `CONFIRMADA` para mañana

La gestión de altas y retiros de salas y horarios está deshabilitada en esta
entrega. El Administrador trabaja con las seis salas y los seis horarios de
ejemplo; tampoco puede abrir el formulario de gestión mediante su URL.

Para borrar todos los datos y volver a cargarlos:
```bash
python manage.py seed_data --reset
```

> `db.sqlite3` es local de cada integrante y no se sube a GitHub (está en
> `.gitignore`). Cada uno crea el suyo con los pasos 3 y 4.

## 5. Levantar el servidor

```bash
python manage.py runserver
```

Abre **http://localhost:8000/**

1. Inicia sesión con `admin@salamandra.upb.edu` / `admin123`.
2. Verás las combinaciones sala+horario, las reservas y los bloqueos.
3. En **"Bloquear un horario por mantenimiento"** elige, por ejemplo,
   *Sala de estudio B — 14:30 a 16:30* y escribe un motivo (`Fuga de agua`).
4. Al enviar, el sistema (todo dentro de **una sola transacción**):
   - pasa las reservas `CONFIRMADA` de ese horario a **`POR_MANTENIMIENTO`**
     (sin penalizar al estudiante),
   - cambia `sala_horario.estado_sala_horario` a `MANTENIMIENTO`,
   - registra el bloqueo (quién, motivo, fecha) en la tabla `bloqueos`.
5. Si intentas bloquear el mismo horario otra vez, lo rechaza (ya está en
   mantenimiento). Sin iniciar sesión no se puede llegar al formulario.

Esto corresponde al flujo principal y a las ramas E1/E2 de
`docs/sesion-07-modelos.md`. La validación del rol Administrador se hace al
iniciar sesión **y otra vez** dentro de `block_room_schedule_for_maintenance()`
(`reservas/services.py`), para que la regla de negocio no dependa solo de la
pantalla de login.

## 6. Ver el contenido de la base de datos (opcional)

PyCharm puede abrir `db.sqlite3` directamente (doble clic sobre el archivo,
o pestaña **Database** → **+** → **Data Source** → **SQLite**). También
sirve la extensión *SQLite Viewer* de VS Code, o la app gratuita
*DB Browser for SQLite*.

## 7. Pruebas de las reglas de negocio (Sesión 04–06)

Independientes de Django y de la base de datos:
```bash
python -m pytest -q
```

---

## 8. Problemas frecuentes

| Mensaje | Causa y solución |
|---|---|
| `no such table: usuarios` (o la pantalla "No se pudo usar la base de datos") | Faltan las tablas. Ejecuta `makemigrations reservas` y `migrate` (paso 3). |
| `No module named 'django'` | Falta instalar dependencias, o el venv no está activado. Paso 2. |
| En el login: "Correo o contraseña incorrectos" | No corriste `seed_data`, o el correo no es exactamente `admin@salamandra.upb.edu`. |
| Quiero empezar de cero | Borra el archivo `db.sqlite3` y repite los pasos 3 y 4. |

## 9. Estructura del proyecto

```
manage.py
salamandra_project/            Configuración de Django (settings.py: SQLite)
reservas/                      App web (Sesión 07)
    models.py                    Tablas del equipo (ORM de Django)
    services.py                  Caso de uso RES-CU-02 (bloqueo por mantenimiento)
    views.py                     Login, dashboard, bloqueo
    urls.py
    migrations/                  Migraciones (se genera 0001_initial.py)
    templates/reservas/          HTML
    management/commands/seed_data.py   Datos de ejemplo
proyecto/                      Reglas de negocio puras (Sesión 04-06)
tests/                         Pruebas pytest de esas reglas
docs/                          Requisitos, modelos y planes por sesión
db.sqlite3                     Se crea al ejecutar migrate (no se sube a git)
```

## 10. Limitaciones actuales (a propósito)

- Hay pruebas automatizadas de reservas, mantenimiento, sanciones y auditoría.
- Las cancelaciones tardías generan sanciones escalares y el Administrador
  puede aplicar sanciones manuales, retirarlas o reiniciar los contadores.
  El historial de sanciones se conserva siempre en estas operaciones.
- Solo hay un Administrador (creado por `seed_data`); no hay pantalla para
  crear más usuarios o roles.
- No se notifica a los estudiantes cuando su reserva pasa a
  `POR_MANTENIMIENTO` (pregunta pendiente con Sergio).
- El Administrador puede sacar un horario de mantenimiento desde la interfaz;
  el registro del bloqueo se conserva como historial y las reservas que ya
  pasaron a `POR_MANTENIMIENTO` no se restauran automáticamente.

### Reinicio de sanciones y semestres

El 1 de enero y el 1 de julio a las 00:00 (America/La_Paz), los contadores
comienzan en cero y las sanciones del semestre anterior dejan de bloquear.
Se calcula por fecha en cada consulta; no requiere un proceso programado ni
tener el servidor encendido a medianoche. Los registros anteriores, su origen,
responsable y fechas originales permanecen en la base de datos.

El botón **Reiniciar sanciones y contadores** registra un corte manual en
`reinicios_sanciones` (fecha y administrador). Retira las sanciones vigentes
guardando `fecha_retiro` y `retirada_por`; no cambia `fecha_fin` ni borra filas.
Las faltas anteriores al corte dejan de contar para la escala automática.
**Retirar sanción** hace lo mismo para una sanción individual, pero no reinicia
el contador de faltas. El retiro automático por cambio de semestre no rellena
esos dos campos, reservados para retiros manuales.

Las nuevas sanciones manuales ofrecen las cuatro duraciones: 24 horas,
48 horas, una semana y semestre completo. Las sanciones históricas se conservan.
Una sanción deja de bloquear al terminar su plazo, al retirarse manualmente
o al comenzar el siguiente semestre, lo que suceda primero.

`tipo_sancion` es un catálogo fijo y no crece al aplicar sanciones: ID 74
(24 horas), 75 (48 horas), 76 (168 horas) y 77 (semestre completo, 9999
horas). Tanto las sanciones automáticas como las manuales referencian uno de
esos cuatro registros. La base de datos rechaza cualquier ID o duración fuera
de esa correspondencia.

Para actualizar una instalación existente: `python manage.py migrate`.
