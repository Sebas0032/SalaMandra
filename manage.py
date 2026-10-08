#!/usr/bin/env python
"""Utilidad de línea de comandos de Django para SalaMandra."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "salamandra_project.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. ¿Está instalado y activado el entorno "
            "virtual? Ejecuta: pip install -r requirements.txt"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
