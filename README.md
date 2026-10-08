# SalaMandra — Reserva de Salas de Estudio

Proyecto de Ingeniería de Software (P02 — Reservas de espacios),
adaptado a un sistema de reserva de salas de estudio universitarias.

## Integrantes
| Integrante | GitHub |
|---|---|
| Luciana Soza | @luci-solar34 |
| Sebastian Cruz | @Sebas0032 |
| Sebastian Toledo | @sebas-sst |

## Estado actual del proyecto

Este repo contiene **dos partes independientes**:

1. **`proyecto/` + `tests/`** — las reglas de negocio puras en Python
   (Sesiones 04–06: crear reserva, validar estudiante, conflictos de
   horario, capacidad). No tienen interfaz ni base de datos; se
   comprueban con pytest.

2. **`salamandra_project/` + `reservas/`** — la interfaz web funcional
   que implementa el **único caso de uso de la Sesión 07**
   (`docs/sesion-07-modelos.md`, RES-CU-02): un **Administrador** inicia
   sesión y **bloquea el horario de una sala por mantenimiento**, lo que
   cancela automáticamente (sin penalización) la reserva asociada a ese
   horario, si existe.

   ⚠️ **Alcance:** esto llega hasta la Sesión 07. El plan de tareas de las
   Sesiones 08–09 (`docs/sesion-08-09-plan-salamandra_dias.md`) describe
   el *siguiente* incremento (pruebas automatizadas, estimaciones, etc.)
   y **todavía no está implementado a propósito** — queda para la
   siguiente iteración.

### Decisión técnica importante: MongoDB, sin el ORM de Django

El equipo decidió usar **MongoDB** como base de datos. Por eso:

- Se usa Django **solo como framework web** (rutas, vistas, plantillas,
  sesiones).
- El acceso a datos se hace **directamente con `pymongo`**
  (ver `reservas/mongo.py` y `reservas/services.py`), **sin** usar
  `django.db.models` ni ejecutar `python manage.py migrate`.
- Por la misma razón, **no están instaladas** las apps
  `django.contrib.admin`, `django.contrib.auth` ni
  `django.contrib.contenttypes` (todas dependen del ORM). El login de
  Administrador se implementó a mano, guardando el usuario en MongoDB y
  la sesión en una cookie firmada de Django (no requiere base de datos
  relacional).

---

## 1. Qué necesitas instalar

| Herramienta | Para qué | Versión sugerida |
|---|---|---|
| **Python** | Ejecutar Django y las pruebas | 3.10 o superior |
| **pip** | Instalar las librerías de `requirements.txt` | viene con Python |
| **MongoDB** (local o Atlas) | Guardar salas, reservas, bloqueos y el usuario Administrador | MongoDB 6 o 7 |
| **git** | Clonar/subir el repo | cualquiera reciente |

Todo lo demás (Django, pymongo) se instala con `pip install -r requirements.txt` más abajo.

### 1.1. Instalar MongoDB

Elige **una** de estas dos opciones:

**Opción A — MongoDB local (recomendada para el curso)**

- **Windows:** descarga el instalador "MongoDB Community Server" desde
  https://www.mongodb.com/try/download/community, instálalo dejando
  marcada la opción "Install MongoDB as a Service" (así se inicia solo).
- **macOS (con Homebrew):**
  ```bash
  brew tap mongodb/brew
  brew install mongodb-community
  brew services start mongodb-community
  ```
- **Linux (Ubuntu/Debian):** sigue la guía oficial
  https://www.mongodb.com/docs/manual/administration/install-on-linux/
  (el paquete se llama `mongodb-org`) y luego:
  ```bash
  sudo systemctl start mongod
  sudo systemctl enable mongod   # para que arranque solo
  ```

Para confirmar que MongoDB está corriendo:
```bash
mongosh --eval "db.runCommand({ ping: 1 })"
```
Si responde algo como `{ ok: 1 }`, está funcionando en
`mongodb://localhost:27017/`, que es lo que este proyecto usa por defecto.

**Opción B — MongoDB Atlas (en la nube, sin instalar nada local)**

1. Crea un clúster gratuito en https://www.mongodb.com/cloud/atlas/register
2. En "Network Access", agrega tu IP (o `0.0.0.0/0` solo para pruebas).
3. Copia tu cadena de conexión (botón "Connect" → "Drivers"), se ve así:
   `mongodb+srv://usuario:contraseña@cluster0.xxxxx.mongodb.net/`
4. Define esa cadena como variable de entorno `MONGO_URI` (ver sección 3).

---

## 2. Preparar el entorno de Python

```bash
python3 -m venv .venv
source .venv/bin/activate      # En Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

Esto instala `django`, `pymongo` y `pytest`.

---

## 3. Configuración (opcional)

Por defecto, el proyecto se conecta a `mongodb://localhost:27017/` y usa
la base de datos `salamandra_db`. Si usas MongoDB Atlas o quieres otro
nombre de base de datos, define estas variables de entorno **antes** de
correr cualquier comando:

```bash
# Linux/macOS
export MONGO_URI="mongodb+srv://usuario:contraseña@tu-cluster.mongodb.net/"
export MONGO_DB_NAME="salamandra_db"

# Windows (PowerShell)
$env:MONGO_URI = "mongodb+srv://usuario:contraseña@tu-cluster.mongodb.net/"
$env:MONGO_DB_NAME = "salamandra_db"
```

Si no las defines, se usan los valores por defecto (MongoDB local) y no
necesitas hacer nada en este paso.

---

## 4. Cargar datos de ejemplo

Con MongoDB corriendo y el entorno virtual activado:

```bash
python manage.py seed_data
```

Esto crea, **solo si no existen todavía**, siguiendo el modelo de datos
del equipo (`usuarios`, `roles`, `usuarios_roles`, `tipo_sancion`, `salas`,
`horarios`, `sala_horario`, `reservas`, `bloqueos`):

- 2 roles: `Administrador` y `Estudiante`
- 2 usuarios:
  - **Administrador:** `admin@salamandra.upb.edu` / `admin123`
  - Estudiante: Luciana Perez (sin login, solo tiene reservas a su nombre)
- Catálogo `tipo_sancion` (la escala de `docs/sesion-06-requisitos.md`:
  24h, 48h, 1 semana, semestre) — cargado como catálogo, pero su lógica
  (RES-RF-02) todavía no está implementada, queda para otra iteración
- 2 salas: *Sala de estudio A* y *Sala de estudio B*
- 2 horarios: `10:00-12:00` y `15:00-17:00`
- 2 combinaciones `sala_horario` (Sala A + 10:00-12:00, Sala B + 15:00-17:00)
- 2 reservas `CONFIRMADA` de ejemplo, una por cada combinación

Si quieres borrar todo y empezar de cero:
```bash
python manage.py seed_data --reset
```

> **Nota sobre el campo `password_hash`:** el diagrama entidad-relación
> que diseñaron no incluye una columna de contraseña en `usuarios`. Se
> agregó ese único campo porque el login necesita guardarla de alguna
> forma — es la única diferencia respecto al esquema que definieron.
>
> **Nota sobre las llaves foráneas:** en el DDL que generaron, algunas
> `FOREIGN KEY` de `sala_horario`, `reservas` y `bloqueos` apuntan a la
> columna equivocada (por ejemplo, `sala_horario.id_sala_horario`
> referenciando `salas.id_salas`, cuando lógicamente debería ser
> `id_sala` el que referencia `salas`). Esto es común cuando el DDL se
> genera automáticamente con una herramienta tipo dbdiagram.io y se
> reordenan o repiten nombres de columnas. Aquí se implementó la
> relación **lógica correcta** (`id_sala` → `salas.id_salas`,
> `id_horario` → `horarios.id_horario`, `id_sala_horario` en `reservas`
> y `bloqueos` → `sala_horario.id_sala_horario`), manteniendo los mismos
> nombres de columna que definieron. No tienen que cambiar nada; es solo
> para que lo tengan en cuenta si Sergio pregunta por el diagrama.

> ⚠️ **No ejecuten `python manage.py migrate`.** Este proyecto no usa la
> base de datos relacional de Django (ver la nota técnica arriba), así
> que ese comando no aplica aquí y va a fallar — es esperado, no es un
> error en el código.

---

## 5. Levantar el servidor

```bash
python manage.py runserver
```

Abre tu navegador en **http://localhost:8000/**

1. Te va a pedir iniciar sesión → usa `admin@salamandra.upb.edu` / `admin123`.
2. Verás el panel con: las combinaciones sala+horario (`sala_horario`),
   las reservas y los horarios ya bloqueados por mantenimiento.
3. En "Bloquear un horario por mantenimiento", selecciona en el
   desplegable, por ejemplo, **"Sala de estudio B — 15:00 a 17:00
   (DISPONIBLE)"** y escribe un motivo, por ejemplo `Fuga de agua`.
4. Al enviar el formulario, el sistema:
   - Busca las reservas `CONFIRMADA` de esa combinación sala+horario y
     las cambia a **`POR_MANTENIMIENTO`** (sin penalizar al estudiante).
   - Cambia el estado de esa fila de `sala_horario` a `MANTENIMIENTO`.
   - Registra el bloqueo (quién, motivo, fecha) en `bloqueos`.
   - Si intentas bloquear la misma combinación dos veces, lo rechaza
     (ya está en mantenimiento).
   - Si envían un `id_sala_horario` que no existe, lo rechaza.

Esto corresponde al flujo principal y las ramas E1/E2 de
`docs/sesion-07-modelos.md` (RES-CU-02). La validación de rol
(Administrador) se hace tanto al iniciar sesión como otra vez dentro de
`block_room_schedule_for_maintenance()` en `services.py`, para que la
regla de negocio no dependa únicamente de la pantalla de login.

---

## 6. Ejecutar las pruebas de las reglas de negocio (Sesión 04–06)

Estas pruebas son independientes de Django/MongoDB — prueban las
funciones puras de `proyecto/reglas.py`:

```bash
python -m pytest -q
```

---

## 7. Estructura del proyecto

```
manage.py                      Punto de entrada de Django
salamandra_project/            Configuración del proyecto Django
    settings.py                 DATABASES vacío a propósito (se usa MongoDB, no el ORM)
    urls.py
reservas/                      App de Django: la interfaz web (Sesión 07)
    mongo.py                     Conexión a MongoDB (pymongo)
    services.py                  Lógica del caso de uso RES-CU-02 (bloqueo por mantenimiento)
    views.py                     Login de Administrador, dashboard, bloqueo
    urls.py
    templates/reservas/          HTML (login, dashboard, error de conexión)
    management/commands/
        seed_data.py              Carga datos de ejemplo en MongoDB
proyecto/                       Reglas de negocio puras (Sesión 04-06, sin DB ni UI)
tests/                          Pruebas pytest de esas reglas
docs/                            Registro de requisitos, modelos y planes por sesión
```

## 8. Limitaciones actuales (a propósito, quedan para después)

- No hay pruebas automatizadas todavía para el flujo de bloqueo por
  mantenimiento (eso es parte del plan de las Sesiones 08–09, que se
  dejó pendiente intencionalmente).
- Las colecciones `tipo_sancion` y `sanciones` están en el modelo de
  datos (y `tipo_sancion` se carga con el catálogo de `seed_data`), pero
  la lógica de RES-RF-02 (penalizar cancelaciones tardías) **no está
  implementada todavía** — esta iteración solo cubre RES-RF-03
  (bloqueo por mantenimiento).
- Solo existe un usuario Administrador fijo (creado por `seed_data`); no
  hay una pantalla para crear más administradores ni roles adicionales.
- No se envían notificaciones a los estudiantes cuando su reserva pasa a
  `POR_MANTENIMIENTO` (pregunta pendiente con Sergio, ver
  `docs/sesion-07-modelos.md`, sección 6).
- No hay una forma de "desbloquear" un horario desde la interfaz todavía.
