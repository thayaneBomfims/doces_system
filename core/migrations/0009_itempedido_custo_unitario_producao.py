from decimal import Decimal

from django.db import migrations, models


def preencher_custo_unitario_producao(apps, schema_editor):
    ItemPedido = apps.get_model('core', 'ItemPedido')
    Receita = apps.get_model('core', 'Receita')

    itens = ItemPedido.objects.select_related('produto').all()
    for item in itens:
        receitas = Receita.objects.select_related('ingrediente').filter(produto=item.produto)
        custo = sum(
            (Decimal(r.quantidade) * Decimal(r.ingrediente.custo_unitario) for r in receitas),
            Decimal('0')
        )
        item.custo_unitario_producao = custo
        item.save(update_fields=['custo_unitario_producao'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_pedido_desconto_pedido_forma_pagamento'),
    ]

    operations = [
        migrations.AddField(
            model_name='itempedido',
            name='custo_unitario_producao',
            field=models.DecimalField(decimal_places=4, default=0, max_digits=10),
        ),
        migrations.RunPython(preencher_custo_unitario_producao, migrations.RunPython.noop),
    ]
