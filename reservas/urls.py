from django.urls import path

from . import views

urlpatterns = [
    path("salas/", views.student_panel_view, name="student_panel"),
    path("", views.dashboard_view, name="dashboard"),
    path("bloquear/", views.block_room_view, name="block_room"),
]
