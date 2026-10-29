from django.urls import path

from . import views

urlpatterns = [
    path("operante/", views.operator_panel_view, name="operator_panel"),
    path(
        "operante/mantenimiento/<int:id_sala_horario>/habilitar/",
        views.operator_unblock_room_view,
        name="operator_unblock_room",
    ),
    path("salas/", views.student_panel_view, name="student_panel"),
    path(
        "reservas/<int:id_reserva>/modificar/",
        views.modify_reservation_view,
        name="modify_reservation",
    ),
    path(
        "reservas/<int:id_reserva>/cancelar/",
        views.cancel_reservation_view,
        name="cancel_reservation",
    ),
    path("", views.dashboard_view, name="dashboard"),
    path("bloquear/", views.block_room_view, name="block_room"),
    path(
        "mantenimiento/<int:id_sala_horario>/habilitar/",
        views.unblock_room_view,
        name="unblock_room",
    ),
    path("gestion/salas/", views.gestion_salas_view, name="gestion_salas"),
    path(
        "administracion/cancelaciones/",
        views.admin_cancellations_view,
        name="admin_cancellations",
    ),
    path(
        "administracion/cancelaciones/<int:id_reserva>/cancelar/",
        views.admin_cancel_reservation_view,
        name="admin_cancel_reservation",
    ),
    path(
        "administracion/sanciones/",
        views.sanctions_admin_view,
        name="sanctions_admin",
    ),
    path(
        "administracion/sanciones/aplicar/",
        views.apply_sanction_view,
        name="apply_sanction",
    ),
    path(
        "administracion/sanciones/reiniciar/",
        views.clear_sanctions_view,
        name="clear_sanctions",
    ),
    path(
        "administracion/solicitantes/<int:codigo_usuario>/estado/",
        views.change_student_status_view,
        name="change_student_status",
    ),
]
