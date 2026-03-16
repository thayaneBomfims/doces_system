from django.contrib import admin
from django.urls import path
from core.views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard),
    path('importar/', importar_planilha),
    path('ingredientes/', ingredientes),
    path('ingredientes/<int:ingrediente_id>/excluir/', ingrediente_excluir),
    path('compras/<int:compra_id>/excluir/', compra_excluir),
    path('produto/novo/', produto_novo),
    path('produtos/', produtos),
    path('produtos/<int:produto_id>/editar/', produto_editar),
    path('produtos/<int:produto_id>/excluir/', produto_excluir),
    path('produtos/<int:produto_id>/receita', receita_produto),
    path('compras/', compras),
    # Pedidos
    path('pedidos/', pedidos),
    path('pedidos/novo/', pedido_novo),
    path('pedidos/<int:pedido_id>/', pedido_detalhe),
    path('pedidos/<int:pedido_id>/excluir/', pedido_excluir),
    # Agenda
    path('agenda/', agenda),
    # Público
    path('catalogo/', catalogo),
    path('pedido/consulta/', consulta_pedido),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)