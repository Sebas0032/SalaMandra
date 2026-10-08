"""
Este archivo se deja vacío a propósito.

Django exige que cada app tenga un módulo `models.py`, pero este proyecto
NO usa el ORM de Django (no hay clases que hereden de `django.db.models.Model`).

La persistencia de datos —salas, reservas, bloqueos de mantenimiento y el
usuario Administrador— se maneja directamente contra MongoDB usando
`pymongo`. Para ver cómo:

- La conexión a MongoDB:        reservas/mongo.py
- Las colecciones y la lógica
  de negocio (caso de uso
  RES-CU-02 de docs/sesion-07-modelos.md): reservas/services.py
- Las vistas que usan esa
  lógica:                       reservas/views.py

Esta decisión viene de la Sesión 07: el equipo eligió MongoDB en vez del
ORM de Django para este proyecto.
"""
