"""Reglas administrativas para sanciones y estado de los solicitantes."""

from datetime import datetime, timedelta

from django.db import transaction
from django.db.models import Prefetch, Q
from django.utils import timezone

from cuentas.services import ROL_ADMINISTRADOR

from .models import ReinicioSanciones, Sancion, TipoSancion, Usuario


ROLES_SOLICITANTE = ("Solicitante",)

OPCIONES_DURACION = (
    ("24_horas", "24 horas", 24),
    ("48_horas", "48 horas", 48),
    ("1_semana", "1 semana", 168),
    ("semestre", "Semestre completo", 9999),
)

_TIPOS_POR_CODIGO = {
    codigo: (etiqueta, horas, TipoSancion.ID_POR_DURACION[horas])
    for codigo, etiqueta, horas in OPCIONES_DURACION
}


class GestionSancionesError(Exception):
    """Rechazo esperado de una operación administrativa de sanciones."""


def inicio_semestre(ahora):
    """Corte automático a medianoche local del 1 de enero o del 1 de julio."""
    local = timezone.localtime(ahora)
    mes = 1 if local.month < 7 else 7
    return timezone.make_aware(datetime(local.year, mes, 1))


def contar_faltas(usuario, ahora):
    """Cuenta faltas automáticas desde el semestre o el último reinicio manual."""
    corte = inicio_semestre(ahora)
    reinicio = ReinicioSanciones.objects.filter(
        fecha__gte=corte, fecha__lte=ahora
    ).order_by("-fecha", "-pk").first()
    faltas = Sancion.objects.filter(
        usuario=usuario, origen=Sancion.Origen.AUTOMATICA,
        fecha_inicio__gte=corte, fecha_inicio__lte=ahora,
    )
    if reinicio:
        faltas = faltas.filter(fecha_inicio__gt=reinicio.fecha)
    return faltas.count()


def sanciones_vigentes(ahora):
    """Las sanciones de semestres anteriores ya no bloquean, sin borrarlas."""
    return Sancion.objects.filter(
        fecha_retiro__isnull=True,
        fecha_inicio__gte=inicio_semestre(ahora),
        fecha_inicio__lte=ahora, fecha_fin__gt=ahora,
    )


def get_solicitantes(termino="", filtro="todos", ahora=None):
    """Devuelve solicitantes con su sanción vigente y estado de cuenta."""
    ahora = ahora or timezone.localtime()
    sanciones_activas = sanciones_vigentes(ahora).select_related(
        "tipo_sancion"
    ).order_by("-fecha_fin")

    usuarios = Usuario.objects.filter(
        rol__nombre_rol__in=ROLES_SOLICITANTE
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
    administrador = _obtener_administrador(codigo_admin)
    solicitante = _obtener_solicitante(codigo_solicitante, bloquear=True)

    try:
        _, horas, tipo_id = _TIPOS_POR_CODIGO[codigo_duracion]
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
    try:
        tipo_sancion = TipoSancion.objects.get(pk=tipo_id, duracion=horas)
    except TipoSancion.DoesNotExist as exc:
        raise GestionSancionesError(
            "El catálogo de sanciones está incompleto. Ejecuta las migraciones."
        ) from exc
    return Sancion.objects.create(
        usuario=solicitante,
        origen=Sancion.Origen.MANUAL,
        aplicada_por=administrador,
        tipo_sancion=tipo_sancion,
        motivo=motivo,
        fecha_inicio=ahora,
        fecha_fin=ahora + timedelta(hours=horas),
    )


@transaction.atomic
def clear_all_sanctions(codigo_admin):
    """Reinicia contadores y retira sanciones vigentes conservando el historial."""
    administrador = _obtener_administrador(codigo_admin)
    ahora = timezone.localtime()
    ReinicioSanciones.objects.create(fecha=ahora, administrador=administrador)
    cantidad = sanciones_vigentes(ahora).update(
        fecha_retiro=ahora, retirada_por=administrador
    )
    return cantidad


@transaction.atomic
def withdraw_sanction(codigo_admin, id_sancion):
    """Retira una sanción vigente; conserva sus fechas originales y su falta."""
    administrador = _obtener_administrador(codigo_admin)
    ahora = timezone.localtime()
    actualizadas = sanciones_vigentes(ahora).filter(pk=id_sancion).update(
        fecha_retiro=ahora, retirada_por=administrador
    )
    if not actualizadas:
        raise GestionSancionesError("La sanción no existe o ya no está vigente.")


@transaction.atomic
def set_student_active_status(codigo_admin, codigo_solicitante, activo):
    """Activa o desactiva la cuenta de un solicitante."""
    _obtener_administrador(codigo_admin)
    solicitante = _obtener_solicitante(codigo_solicitante, bloquear=True)
    solicitante.estado_usuario = bool(activo)
    solicitante.save(update_fields=["estado_usuario"])
    return solicitante


def _obtener_administrador(codigo_admin):
    administrador = Usuario.objects.filter(
        pk=codigo_admin,
        estado_usuario=True,
        rol__nombre_rol=ROL_ADMINISTRADOR,
    ).distinct().first()
    if administrador is None:
        raise GestionSancionesError(
            "Solo un Administrador activo puede realizar esta operación."
        )
    return administrador


def _obtener_solicitante(codigo_solicitante, bloquear=False):
    consulta = Usuario.objects.filter(
        pk=codigo_solicitante,
        rol__nombre_rol__in=ROLES_SOLICITANTE,
    ).distinct()
    if bloquear:
        consulta = consulta.select_for_update()
    solicitante = consulta.first()
    if solicitante is None:
        raise GestionSancionesError(
            "No existe un solicitante con el código indicado."
        )
    return solicitante
