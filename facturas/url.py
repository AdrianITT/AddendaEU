from django.urls import path
from .views import agregar_addenda

urlpatterns = [
    path('agregar_addenda/<str:factura_name>/', agregar_addenda, name='agregar_addenda'),
]
