import pytest


def pytest_collection_modifyitems(items):
    """Clasifica como unitaria toda prueba que no declare otra capa."""
    for item in items:
        es_integracion = item.get_closest_marker("integration") is not None
        es_e2e = item.get_closest_marker("e2e") is not None
        if not es_integracion and not es_e2e:
            item.add_marker(pytest.mark.unit)


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
