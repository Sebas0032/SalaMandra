from django.urls import path, include

urlpatterns = [
    path("", include("cuentas.urls")),
    path("", include("reservas.urls")),
]
