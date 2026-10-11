"""
Modelos de SalaMandra: el diagrama entidad-relación del equipo, tal cual,
como tablas de SQLite (mismos nombres de tabla y de columna).

    roles, usuarios, usuarios_roles, tipo_sancion, sanciones,
    horarios, salas, sala_horario, reservas, bloqueos

Notas:
- `usuarios.password_hash` NO está en el diagrama original del equipo. Se
  agregó solo porque el login necesita guardar la contraseña.
- En el DDL original algunas FOREIGN KEY de `sala_horario`, `reservas` y
  `bloqueos` apuntaban a la columna equivocada. Aquí se implementó la
  relación lógica correcta:
      sala_horario.id_sala        -> salas.id_salas
      sala_horario.id_horario     -> horarios.id_horario
      reservas.id_sala_horario    -> sala_horario.id_sala_horario
      bloqueos.id_sala_horario    -> sala_horario.id_sala_horario
- `tipo_sancion` y `sanciones` existen como tablas, pero la lógica para
  aplicar sanciones (RES-RF-02) todavía no está implementada.
"""

from django.db import models
from django.utils import timezone


class Rol(models.Model):
    id_rol = models.AutoField(primary_key=True)
    nombre_rol = models.CharField(max_length=100)

    class Meta:
        db_table = "roles"

    def __str__(self):
        return self.nombre_rol


class Usuario(models.Model):
    codigo_usuario = models.AutoField(primary_key=True)
    email = models.CharField(max_length=255, unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    estado_usuario = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    # Campo agregado (no está en el diagrama original), necesario para el login.
    password_hash = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "usuarios"

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


class UsuarioRol(models.Model):
    id_usuario_roles = models.AutoField(primary_key=True)
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE, db_column="id_rol")
    usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, db_column="codigo_usuario"
    )

    class Meta:
        db_table = "usuarios_roles"


class TipoSancion(models.Model):
    id_tipo_sancion = models.AutoField(primary_key=True)
    nombre_sancion = models.CharField(max_length=200)
    duracion = models.IntegerField()  # en horas

    class Meta:
        db_table = "tipo_sancion"

    def __str__(self):
        return self.nombre_sancion


class Sancion(models.Model):
    id_sancion = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(
        Usuario, on_delete=models.PROTECT, db_column="codigo_usuario"
    )
    tipo_sancion = models.ForeignKey(
        TipoSancion, on_delete=models.PROTECT, db_column="id_tipo_sancion"
    )
    motivo = models.CharField(max_length=255)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()

    class Meta:
        db_table = "sanciones"


class Horario(models.Model):
    id_horario = models.AutoField(primary_key=True)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    class Meta:
        db_table = "horarios"

    def __str__(self):
        return f"{self.hora_inicio:%H:%M}-{self.hora_fin:%H:%M}"


class Sala(models.Model):
    id_salas = models.AutoField(primary_key=True)
    nombre_sala = models.CharField(max_length=100)
    estado_sala = models.BooleanField(default=True)

    class Meta:
        db_table = "salas"

    def __str__(self):
        return self.nombre_sala


class SalaHorario(models.Model):
    ESTADO_DISPONIBLE = "DISPONIBLE"
    ESTADO_MANTENIMIENTO = "MANTENIMIENTO"

    id_sala_horario = models.AutoField(primary_key=True)
    sala = models.ForeignKey(Sala, on_delete=models.PROTECT, db_column="id_sala")
    horario = models.ForeignKey(
        Horario, on_delete=models.PROTECT, db_column="id_horario"
    )
    estado_sala_horario = models.CharField(max_length=100, default=ESTADO_DISPONIBLE)

    class Meta:
        db_table = "sala_horario"
        constraints = [
            models.UniqueConstraint(
                fields=["sala", "horario"], name="uq_sala_horario_sala_horario"
            )
        ]

    def __str__(self):
        return f"{self.sala} {self.horario}"


class Reserva(models.Model):
    ESTADO_CONFIRMADA = "CONFIRMADA"
    ESTADO_POR_MANTENIMIENTO = "POR_MANTENIMIENTO"

    id_reserva = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(
        Usuario, on_delete=models.PROTECT, db_column="codigo_usuario"
    )
    sala_horario = models.ForeignKey(
        SalaHorario, on_delete=models.PROTECT, db_column="id_sala_horario"
    )
    tipo_actividad = models.CharField(max_length=255)
    fecha = models.DateField()
    estado_reserva = models.CharField(max_length=70, default=ESTADO_CONFIRMADA)

    class Meta:
        db_table = "reservas"


class Bloqueo(models.Model):
    id_bloqueo = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(
        Usuario, on_delete=models.PROTECT, db_column="codigo_usuario"
    )
    sala_horario = models.ForeignKey(
        SalaHorario, on_delete=models.PROTECT, db_column="id_sala_horario"
    )
    motivo = models.CharField(max_length=200)
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "bloqueos"
