"""
Modelos de SalaMandra: el diagrama entidad-relación del equipo, tal cual,
como tablas de SQLite (mismos nombres de tabla y de columna).

    roles, usuarios, tipo_sancion, sanciones,
    horarios, salas, sala_horario, reservas, auditoria, bloqueos

Notas:
- `usuarios.password_hash` NO está en el diagrama original del equipo. Se
  agregó solo porque el login necesita guardar la contraseña.
- En el DDL original algunas FOREIGN KEY de `sala_horario`, `reservas` y
  `bloqueos` apuntaban a la columna equivocada. Aquí se implementó la
  relación lógica correcta:
      sala_hogrario.id_sala        -> salas.id_salas
      sala_horario.id_horario     -> horarios.id_horario
      reservas.id_sala_horario    -> sala_horario.id_sala_horario
      bloqueos.id_sala_horario    -> sala_horario.id_sala_horario
- La lógica de sanciones automáticas y manuales utiliza `tipo_sancion` y
  `sanciones` mediante el ORM de Django.
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower, Trim
from django.utils import timezone


class Rol(models.Model):
    class Nombre(models.TextChoices):
        ADMINISTRADOR = "Administrador", "Administrador"
        OPERANTE = "Operante", "Operante"
        SOLICITANTE = "Solicitante", "Solicitante"

    id_rol = models.AutoField(primary_key=True)
    nombre_rol = models.CharField(max_length=100, choices=Nombre.choices, unique=True)

    class Meta:
        db_table = "roles"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(nombre_rol__in=["Administrador", "Operante", "Solicitante"]),
                name="rol_nombre_permitido",
            ),
        ]

    def __str__(self):
        return self.nombre_rol


class Usuario(models.Model):
    codigo_usuario = models.BigIntegerField(primary_key=True)
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT, db_column="id_rol")
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


class TipoSancion(models.Model):
    id_tipo_sancion = models.AutoField(primary_key=True)
    nombre_sancion = models.CharField(max_length=200)
    duracion = models.IntegerField()  # en horas

    class Meta:
        db_table = "tipo_sancion"

    def __str__(self):
        return self.nombre_sancion


class Sancion(models.Model):
    class Origen(models.TextChoices):
        AUTOMATICA = "AUTOMATICA", "Automática"
        MANUAL = "MANUAL", "Manual"

    id_sancion = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(
        Usuario, on_delete=models.PROTECT, db_column="codigo_usuario"
    )
    tipo_sancion = models.ForeignKey(
        TipoSancion, on_delete=models.PROTECT, db_column="id_tipo_sancion"
    )
    aplicada_por = models.ForeignKey(
        Usuario, on_delete=models.PROTECT, db_column="aplicada_por",
        related_name="sanciones_aplicadas", null=True, blank=True,
    )
    origen = models.CharField(max_length=100, choices=Origen.choices)
    motivo = models.CharField(max_length=255)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()

    class Meta:
        db_table = "sanciones"
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(origen="AUTOMATICA", aplicada_por__isnull=True)
                    | models.Q(origen="MANUAL", aplicada_por__isnull=False)
                ),
                name="sancion_origen_aplicador_coherente",
            ),
        ]

    def clean(self):
        super().clean()
        if self.origen == self.Origen.MANUAL and self.aplicada_por_id:
            if self.aplicada_por.rol.nombre_rol != Rol.Nombre.ADMINISTRADOR:
                raise ValidationError({"aplicada_por": "Debe ser un administrador."})


class Horario(models.Model):
    id_horario = models.AutoField(primary_key=True)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    class Meta:
        db_table = "horarios"
        constraints = [models.UniqueConstraint(fields=["hora_inicio", "hora_fin"], name="uq_horario_intervalo"),]

    def __str__(self):
        return f"{self.hora_inicio:%H:%M}-{self.hora_fin:%H:%M}"


class Sala(models.Model):
    id_salas = models.AutoField(primary_key=True)
    nombre_sala = models.CharField(max_length=100)
    estado_sala = models.BooleanField(default=True)

    class Meta:
        db_table = "salas"
        constraints = [models.UniqueConstraint(Lower(Trim("nombre_sala")), name="uq_sala_nombre_normalizado"),]

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
    ESTADO_CANCELADA = "CANCELADA"
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
        constraints = [
            models.UniqueConstraint(
                fields=["sala_horario", "fecha"],
                condition=models.Q(estado_reserva__in=["CONFIRMADA", "EN_USO"]),
                name="uq_reserva_activa_horario_fecha",
            ),
        ]


class Auditoria(models.Model):
    class Accion(models.TextChoices):
        CREAR = "CREAR", "Crear"
        CANCELAR = "CANCELAR", "Cancelar"
        MODIFICAR = "MODIFICAR", "Modificar"

    id_auditoria = models.AutoField(primary_key=True)
    reserva = models.ForeignKey(
        Reserva, on_delete=models.PROTECT, db_column="id_reserva",
        related_name="auditorias",
    )
    actor = models.ForeignKey(
        Usuario, on_delete=models.PROTECT, db_column="codigo_actor",
        related_name="acciones_reserva",
    )
    accion = models.CharField(max_length=100, choices=Accion.choices)
    fecha_accion = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "auditoria"
        ordering = ["fecha_accion", "id_auditoria"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(accion__in=["CREAR", "CANCELAR", "MODIFICAR"]),
                name="auditoria_accion_permitida",
            ),
        ]


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
