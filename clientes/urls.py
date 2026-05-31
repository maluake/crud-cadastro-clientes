from django.urls import path
from . import views

urlpatterns = [
    path('', views.listar_clientes, name='listar'),
    path('novo/', views.novo_cliente, name='novo'),
    path('editar/<int:id>/', views.editar_cliente, name='editar'),
    path('excluir/<int:id>/', views.excluir_cliente, name='excluir'),
]