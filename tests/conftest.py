import pytest


@pytest.fixture(autouse=True)
def catalogo_fijo_sanciones(request):
    """Replica los cuatro registros creados por migraciones en pruebas sin ellas."""
    if request.node.get_closest_marker("django_db") is None:
        return

    from reservas.models import TipoSancion

    for tipo_id, nombre, duracion in TipoSancion.CATALOGO:
        TipoSancion.objects.update_or_create(
            pk=tipo_id,
            defaults={"nombre_sancion": nombre, "duracion": duracion},
        )
