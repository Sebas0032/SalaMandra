from django.urls import path

from . import views

urlpatterns = [
    path("salas/", views.student_panel_view, name="student_panel"),
    path(
        "reservas/<int:id_reserva>/modificar/",
        views.modify_reservation_view,
        name="modify_reservation",
    ),
    path("", views.dashboard_view, name="dashboard"),
    path("bloquear/", views.block_room_view, name="block_room"),
    path("/gestion/salas/", views.gestion_salas_view, name="gestion_salas"),
]
