# Reserva de Salas de Estudio

Proyecto de Ingeniería de Software (P02 — Reservas de espacios),
adaptado a un sistema de reserva de salas de estudio universitarias.

## Integrantes
| Integrante | GitHub |
|---|---|
| Luciana Soza | @luci-solar34 |
| Sebastian Cruz | @Sebas0032 |
| Sebastian Toledo | @sebas-sst |
## Estado actual

Fase: definición de requisitos y primera capacidad (Sesión 04).
Reglas de negocio en `proyecto/reglas.py`, sin persistencia ni
interfaz todavía (llegan en fases posteriores del curso).

## Preparar el entorno

```bash
python3 -m venv .venv
source .venv/bin/activate      # En Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Ejecutar las pruebas

```bash
python -m pytest -q
```

## Estructura

```
proyecto/       Reglas de negocio (funciones puras, sin DB ni UI)
tests/          Pruebas de esas reglas
docs/           Registro de acuerdos, ejemplos y retrospectivas
```

## Limitaciones actuales

Sin persistencia en base de datos ni interfaz de usuario todavía;
se incorporarán en fases posteriores del curso.
