"""Reglas administrativas para sanciones y estado de los solicitantes."""

from datetime import timedelta

from django.db import transaction
from django.db.models import Prefetch, Q
from django.utils import timezone

from cuentas.services import ROL_ADMINISTRADOR

from .models import Sancion, TipoSancion, Usuario


ROLES_SOLICITANTE = ("Solicitante", "Estudiante")

OPCIONES_DURACION = (
    ("24_horas", "24 horas", 24),
    ("48_horas", "48 horas", 48),
    ("1_semana", "1 semana", 168),
    ("1_mes", "1 mes", 720),
    ("semestre", "Semestre completo", 9999),
)

_DURACIONES_POR_CODIGO = {
    codigo: (etiqueta, horas)
    for codigo, etiqueta, horas in OPCIONES_DURACION
}


class GestionSancionesError(Exception):
    """Rechazo esperado de una operación administrativa de sanciones."""


def get_solicitantes(termino="", filtro="todos", ahora=None):
    """Devuelve solicitantes con su sanción vigente y estado de cuenta."""
    ahora = ahora or timezone.localtime()
    sanciones_activas = Sancion.objects.filter(
        fecha_inicio__lte=ahora,
        fecha_fin__gt=ahora,
    ).select_related("tipo_sancion").order_by("-fecha_fin")

    usuarios = Usuario.objects.filter(
        usuariorol__rol__nombre_rol__in=ROLES_SOLICITANTE
    ).distinct().prefetch_related(
        Prefetch(
            "sancion_set",
            queryset=sanciones_activas,
            to_attr="sanciones_activas",
        )
    ).order_by("nombre", "apellido", "codigo_usuario")

    termino = termino.strip()
    if termino:
        busqueda = (
            Q(nombre__icontains=termino)
            | Q(apellido__icontains=termino)
            | Q(email__icontains=termino)
        )
        if termino.isdecimal():
            busqueda |= Q(codigo_usuario=int(termino))
        usuarios = usuarios.filter(busqueda)

    filas = []
    for usuario in usuarios:
        sancion = (
            usuario.sanciones_activas[0]
            if usuario.sanciones_activas
            else None
        )
        if filtro == "activos" and not usuario.estado_usuario:
            continue
        if filtro == "inactivos" and usuario.estado_usuario:
            continue
        if filtro == "sancionados" and sancion is None:
            continue
        filas.append({"usuario": usuario, "sancion": sancion})
    return filas


@transaction.atomic
def apply_manual_sanction(
    codigo_admin, codigo_solicitante, codigo_duracion, motivo
):
    """Registra una sanción manual elegida por un Administrador."""
    _obtener_administrador(codigo_admin)
    solicitante = _obtener_solicitante(codigo_solicitante, bloquear=True)

    try:
        etiqueta, horas = _DURACIONES_POR_CODIGO[codigo_duracion]
    except KeyError as exc:
        raise GestionSancionesError(
            "Selecciona una duración de sanción válida."
        ) from exc

    motivo = motivo.strip()
    if not motivo:
        raise GestionSancionesError("El motivo de la sanción es obligatorio.")
    if len(motivo) > 255:
        raise GestionSancionesError(
            "El motivo de la sanción no puede superar 255 caracteres."
        )

    ahora = timezone.localtime()
    tipo_sancion, _ = TipoSancion.objects.get_or_create(
        nombre_sancion=f"Sanción manual ({etiqueta})",
        duracion=horas,
    )
    return Sancion.objects.create(
        usuario=solicitante,
        tipo_sancion=tipo_sancion,
        motivo=motivo,
        fecha_inicio=ahora,
        fecha_fin=ahora + timedelta(hours=horas),
    )


@transaction.atomic
def clear_all_sanctions(codigo_admin):
    """Elimina el historial completo al iniciar un nuevo semestre."""
    _obtener_administrador(codigo_admin)
    cantidad, _ = Sancion.objects.all().delete()
    return cantidad


@transaction.atomic
def set_student_active_status(codigo_admin, codigo_solicitante, activo):
    """Activa o desactiva la cuenta de un solicitante."""
    _obtener_administrador(codigo_admin)
    solicitante = _obtener_solicitante(codigo_solicitante, bloquear=True)
    if solicitante.usuariorol_set.filter(
        rol__nombre_rol=ROL_ADMINISTRADOR
    ).exists():
        raise GestionSancionesError(
            "El estado de una cuenta administradora no se modifica aquí."
        )
    solicitante.estado_usuario = bool(activo)
    solicitante.save(update_fields=["estado_usuario"])
    return solicitante


def _obtener_administrador(codigo_admin):
    administrador = Usuario.objects.filter(
        pk=codigo_admin,
        estado_usuario=True,
        usuariorol__rol__nombre_rol=ROL_ADMINISTRADOR,
    ).distinct().first()
    if administrador is None:
        raise GestionSancionesError(
            "Solo un Administrador activo puede realizar esta operación."
        )
    return administrador


def _obtener_solicitante(codigo_solicitante, bloquear=False):
    consulta = Usuario.objects.filter(
        pk=codigo_solicitante,
        usuariorol__rol__nombre_rol__in=ROLES_SOLICITANTE,
    ).distinct()
    if bloquear:
        consulta = consulta.select_for_update()
    solicitante = consulta.first()
    if solicitante is None:
        raise GestionSancionesError(
            "No existe un solicitante con el código indicado."
        )
    return solicitante
