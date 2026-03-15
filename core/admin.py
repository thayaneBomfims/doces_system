from django.contrib import admin
from .models import *

admin.site.register(Ingrediente)
admin.site.register(Produto)
admin.site.register(Receita)
admin.site.register(Cliente)
admin.site.register(Pedido)
admin.site.register(ItemPedido)