"""
Lógica de negocio del caso de uso RES-CU-02 (docs/sesion-07-modelos.md):
"Bloquear un horario de una sala por mantenimiento".

Colecciones usadas (siguiendo el diagrama entidad-relación del equipo):

    usuarios        codigo_usuario, email, nombre, apellido, estado_usuario,
                    fecha_creacion (+ password_hash, ver nota más abajo)
    roles           id_rol, nombre_rol
    usuarios_roles  id_usuario_roles, id_rol (FK), codigo_usuario (FK)
    tipo_sancion    id_tipo_sancion, nombre_sancion, duracion
                    (catálogo cargado, pero sin lógica implementada todavía:
                     es para RES-RF-02, que queda para otra iteración)
    sanciones       id_sancion, codigo_usuario (FK), id_tipo_sancion (FK),
                    motivo, fecha_inicio, fecha_fin (sin uso todavía)
    salas           id_salas, nombre_sala, estado_sala
    horarios        id_horario, hora_inicio, hora_fin
    sala_horario    id_sala_horario, id_sala (FK), id_horario (FK),
                    estado_sala_horario  (DISPONIBLE / MANTENIMIENTO)
    reservas        id_reserva, codigo_usuario (FK), id_sala_horario (FK),
                    tipo_actividad, fecha, estado_reserva
    bloqueos        id_bloqueo, codigo_usuario (FK, el Administrador),
                    id_sala_horario (FK), motivo, fecha

NOTA sobre `password_hash`: el diagrama original del equipo no tiene un
campo de contraseña en `usuarios`. Se agregó solo ese campo porque el
login necesita guardarla de alguna forma; es la única diferencia respecto
al esquema que enviaron.

NOTA sobre las llaves foráneas de `sala_horario`, `reservas` y `bloqueos`:
en el DDL que compartieron, algunas FOREIGN KEY apuntan a la columna
equivocada (ej. `sala_horario.id_sala_horario` referenciando
`salas.id_salas`, cuando lógicamente debería ser `id_sala` el que
referencia `salas`). Aquí se implementó la relación lógica correcta
(id_sala -> salas.id_salas, id_horario -> horarios.id_horario, etc.),
manteniendo los mismos nombres de columna que enviaron.

Flujo de `block_room_schedule_for_maintenance`, paso a paso según
docs/sesion-07-modelos.md:

    1. El Administrador selecciona la sala y el horario (= un
       id_sala_horario) que quiere bloquear.
    2. El sistema valida que quien lo pide tenga rol Administrador  -> E1
       y que esa combinación sala+horario exista.                  -> E2
    3. El sistema verifica que no esté ya en MANTENIMIENTO.
    4. Busca las reservas CONFIRMADA asociadas a ese id_sala_horario.
    5. Las cambia a POR_MANTENIMIENTO (sin penalización).
    6. Cambia sala_horario.estado_sala_horario a MANTENIMIENTO.
    7. Registra el bloqueo (quién, motivo, fecha) en `bloqueos`.
    8. Confirma el resultado e informa qué reservas se cancelaron.
"""

from datetime import datetime, timezone

from django.contrib.auth.hashers import check_password

from .mongo import get_db, get_next_sequence

ROL_ADMINISTRADOR = "Administrador"


class ScheduleNotFoundError(Exception):
    """No existe esa combinación de sala y horario (rama E2)."""


class NotAuthorizedError(Exception):
    """Quien solicita el bloqueo no tiene rol de Administrador (rama E1)."""


class ScheduleAlreadyBlockedError(Exception):
    """Ese id_sala_horario ya está en estado MANTENIMIENTO."""


# --- Autenticación -----------------------------------------------------

def get_usuario_by_email(email):
    db = get_db()
    return db.usuarios.find_one({"email": email})


def usuario_tiene_rol(codigo_usuario, nombre_rol):
    db = get_db()
    ids_rol = [
        ur["id_rol"] for ur in db.usuarios_roles.find({"codigo_usuario": codigo_usuario})
    ]
    if not ids_rol:
        return False
    return (
        db.roles.find_one({"id_rol": {"$in": ids_rol}, "nombre_rol": nombre_rol})
        is not None
    )


def authenticate_admin(email, password):
    """Devuelve el documento de `usuarios` si el correo/contraseña son
    correctos, la cuenta está activa (estado_usuario) y el usuario tiene
    el rol Administrador. Devuelve None en cualquier otro caso."""
    usuario = get_usuario_by_email(email)
    if not usuario:
        return None
    if not usuario.get("estado_usuario", True):
        return None
    if "password_hash" not in usuario or not check_password(
        password, usuario["password_hash"]
    ):
        return None
    if not usuario_tiene_rol(usuario["codigo_usuario"], ROL_ADMINISTRADOR):
        return None
    return usuario


# --- Lecturas simples, para mostrar el estado del sistema -------------------

def get_salas():
    db = get_db()
    return list(db.salas.find().sort("id_salas", 1))


def get_sala(id_sala):
    db = get_db()
    return db.salas.find_one({"id_salas": id_sala})


def get_horarios():
    db = get_db()
    return list(db.horarios.find().sort("id_horario", 1))


def get_horario(id_horario):
    db = get_db()
    return db.horarios.find_one({"id_horario": id_horario})


def get_sala_horario_por_id(id_sala_horario):
    db = get_db()
    return db.sala_horario.find_one({"id_sala_horario": id_sala_horario})


def get_sala_horarios_con_detalle():
    """Cada combinación sala+horario con el nombre de la sala y las horas
    ya resueltos, para no tener que hacer varias consultas desde las
    plantillas (pymongo no hace JOINs; esto es lo más parecido)."""
    db = get_db()
    salas_por_id = {s["id_salas"]: s for s in db.salas.find()}
    horarios_por_id = {h["id_horario"]: h for h in db.horarios.find()}

    combos = []
    for sh in db.sala_horario.find().sort("id_sala_horario", 1):
        sala = salas_por_id.get(sh["id_sala"])
        horario = horarios_por_id.get(sh["id_horario"])
        combos.append(
            {
                **sh,
                "sala_nombre": sala["nombre_sala"] if sala else "?",
                "hora_inicio": horario["hora_inicio"] if horario else "?",
                "hora_fin": horario["hora_fin"] if horario else "?",
            }
        )
    return combos


def get_reservas_con_detalle():
    db = get_db()
    usuarios_por_codigo = {u["codigo_usuario"]: u for u in db.usuarios.find()}
    combos_por_id = {c["id_sala_horario"]: c for c in get_sala_horarios_con_detalle()}

    reservas = []
    for r in db.reservas.find().sort("id_reserva", 1):
        usuario = usuarios_por_codigo.get(r["codigo_usuario"])
        combo = combos_por_id.get(r["id_sala_horario"])
        reservas.append(
            {
                **r,
                "usuario_nombre": (
                    f"{usuario['nombre']} {usuario['apellido']}" if usuario else "?"
                ),
                "sala_nombre": combo["sala_nombre"] if combo else "?",
                "hora_inicio": combo["hora_inicio"] if combo else "?",
                "hora_fin": combo["hora_fin"] if combo else "?",
            }
        )
    return reservas


def get_bloqueos_con_detalle():
    db = get_db()
    usuarios_por_codigo = {u["codigo_usuario"]: u for u in db.usuarios.find()}
    combos_por_id = {c["id_sala_horario"]: c for c in get_sala_horarios_con_detalle()}

    bloqueos = []
    for b in db.bloqueos.find().sort("fecha", -1):
        usuario = usuarios_por_codigo.get(b["codigo_usuario"])
        combo = combos_por_id.get(b["id_sala_horario"])
        bloqueos.append(
            {
                **b,
                "admin_nombre": (
                    f"{usuario['nombre']} {usuario['apellido']}" if usuario else "?"
                ),
                "sala_nombre": combo["sala_nombre"] if combo else "?",
                "hora_inicio": combo["hora_inicio"] if combo else "?",
                "hora_fin": combo["hora_fin"] if combo else "?",
            }
        )
    return bloqueos


# --- Caso de uso RES-CU-02 --------------------------------------------------

def block_room_schedule_for_maintenance(codigo_usuario_admin, id_sala_horario, motivo):
    """
    Bloquea por mantenimiento una combinación sala+horario (id_sala_horario).

    Parámetros:
        codigo_usuario_admin (int): codigo_usuario de quien pide el bloqueo.
        id_sala_horario (int):      combinación sala+horario a bloquear.
        motivo (str):                razón del bloqueo, ej. "Fuga de agua".

    Devuelve un dict con el resultado. Lanza una excepción si el sistema
    debe rechazar la operación (ramas E1 / E2 / horario ya bloqueado).
    """
    # Paso 2 (parte 1) — E1: sin permisos de Administrador
    if not usuario_tiene_rol(codigo_usuario_admin, ROL_ADMINISTRADOR):
        raise NotAuthorizedError(
            "No tienes permisos para bloquear salas. Contacta al administrador."
        )

    # Paso 2 (parte 2) — E2: la combinación sala+horario no existe
    sala_horario = get_sala_horario_por_id(id_sala_horario)
    if sala_horario is None:
        raise ScheduleNotFoundError(
            f"No existe una combinación de sala y horario con id {id_sala_horario}."
        )

    sala = get_sala(sala_horario["id_sala"])
    horario = get_horario(sala_horario["id_horario"])

    # Paso 3 — el horario ya está en mantenimiento
    if sala_horario.get("estado_sala_horario") == "MANTENIMIENTO":
        raise ScheduleAlreadyBlockedError(
            f"El horario {horario['hora_inicio']}-{horario['hora_fin']} de la "
            f"sala {sala['nombre_sala']} ya está en mantenimiento."
        )

    db = get_db()

    # Paso 4 y 5 — cancelar (sin penalización) las reservas CONFIRMADA
    # asociadas a ese id_sala_horario
    reservas_canceladas = list(
        db.reservas.find(
            {"id_sala_horario": id_sala_horario, "estado_reserva": "CONFIRMADA"}
        )
    )
    for reserva in reservas_canceladas:
        db.reservas.update_one(
            {"id_reserva": reserva["id_reserva"]},
            {"$set": {"estado_reserva": "POR_MANTENIMIENTO"}},
        )

    # Paso 6 — el horario de la sala pasa a MANTENIMIENTO
    db.sala_horario.update_one(
        {"id_sala_horario": id_sala_horario},
        {"$set": {"estado_sala_horario": "MANTENIMIENTO"}},
    )

    # Paso 7 — registrar el bloqueo (quién, motivo, fecha)
    id_bloqueo = get_next_sequence(db, "id_bloqueo")
    db.bloqueos.insert_one(
        {
            "id_bloqueo": id_bloqueo,
            "codigo_usuario": codigo_usuario_admin,
            "id_sala_horario": id_sala_horario,
            "motivo": motivo,
            "fecha": datetime.now(timezone.utc),
        }
    )

    # Paso 8 — confirmar el resultado
    return {
        "sala": sala,
        "horario": horario,
        "reservas_canceladas": reservas_canceladas,
    }
