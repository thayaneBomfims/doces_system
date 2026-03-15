from django.db import models
from datetime import date
from decimal import Decimal, InvalidOperation


# 🧂 INGREDIENTES

class Ingrediente(models.Model):
    nome = models.CharField(max_length=200)
    valor_pacote = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gramas_por_unidade = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    custo_unitario = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    estoque_atual = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        try:
            valor_pacote = Decimal(str(self.valor_pacote or 0))
            gramas_por_unidade = Decimal(str(self.gramas_por_unidade or 0))
        except (InvalidOperation, TypeError, ValueError):
            valor_pacote = Decimal('0')
            gramas_por_unidade = Decimal('0')

        if gramas_por_unidade > 0:
            self.custo_unitario = valor_pacote / gramas_por_unidade
        else:
            self.custo_unitario = Decimal('0')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome


# 🍫 PRODUTOS

class Produto(models.Model):
    nome = models.CharField(max_length=200)
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2)
    imagem = models.ImageField(upload_to='produtos/', blank=True, null=True)

    def __str__(self):
        return self.nome


# 📋 RECEITA (Ficha técnica)

class Receita(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    ingrediente = models.ForeignKey(Ingrediente, on_delete=models.CASCADE)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)

    def custo(self):
        return self.quantidade * self.ingrediente.custo_unitario


# 🛒 COMPRAS (entrada de estoque)

class Compra(models.Model):
    data = models.DateField(default=date.today)
    local = models.CharField(max_length=200, blank=True, default='')

    def __str__(self):
        return f"Compra {self.id} — {self.local} ({self.data})"

class ItemCompra(models.Model):
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE)
    ingrediente = models.ForeignKey(Ingrediente, on_delete=models.CASCADE)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    custo_total = models.DecimalField(max_digits=10, decimal_places=2)

    def quantidade_pacotes(self):
        gramas = Decimal(self.ingrediente.gramas_por_unidade or 0)
        if gramas <= 0:
            return Decimal('0')
        return Decimal(self.quantidade) / gramas
    
class Cliente(models.Model):
    nome = models.CharField(max_length=200)
    telefone = models.CharField(max_length=20)
    endereco = models.TextField(blank=True)

    def __str__(self):
        return self.nome


class Pedido(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    data_pedido = models.DateTimeField(auto_now_add=True)
    data_entrega = models.DateField()
    taxa_entrega = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    desconto = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    forma_pagamento = models.CharField(max_length=50, blank=True, default='')
    status = models.CharField(max_length=50, default="Pendente")
    observacoes = models.TextField(blank=True, default='')
    baixa_estoque_aprovada = models.BooleanField(default=False)

    def __str__(self):
        return f"Pedido {self.id} - {self.cliente}"

    def total(self):
        return sum(i.subtotal() for i in self.itempedido_set.all())

    def total_com_entrega(self):
        total_final = Decimal(self.total()) + Decimal(self.taxa_entrega) - Decimal(self.desconto)
        return total_final if total_final > 0 else Decimal('0')

    def status_badge_class(self):
        return {
            'Pendente': 'badge-yellow',
            'Confirmado': 'badge-blue',
            'Em produção': 'badge-orange',
            'Pronto': 'badge-green',
            'Entregue': 'badge-gray',
            'Cancelado': 'badge-red',
        }.get(self.status, 'badge-purple')


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.IntegerField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.quantidade * self.preco_unitario