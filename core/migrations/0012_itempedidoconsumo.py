from django.db import migrations, models


def popular_snapshot_consumo_itens(apps, schema_editor):
    ItemPedido = apps.get_model('core', 'ItemPedido')
    Receita = apps.get_model('core', 'Receita')
    ItemPedidoConsumo = apps.get_model('core', 'ItemPedidoConsumo')

    for item in ItemPedido.objects.select_related('produto').all():
        receitas = Receita.objects.select_related('ingrediente').filter(produto=item.produto)
        for receita in receitas:
            ItemPedidoConsumo.objects.create(
                item_pedido=item,
                ingrediente=receita.ingrediente,
                ingrediente_nome=receita.ingrediente.nome,
                quantidade_por_unidade=receita.quantidade,
            )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_ingrediente_ativo'),
    ]

    operations = [
        migrations.CreateModel(
            name='ItemPedidoConsumo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ingrediente_nome', models.CharField(max_length=200)),
                ('quantidade_por_unidade', models.DecimalField(decimal_places=2, max_digits=10)),
                ('ingrediente', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, to='core.ingrediente')),
                ('item_pedido', models.ForeignKey(on_delete=models.CASCADE, to='core.itempedido')),
            ],
        ),
        migrations.RunPython(popular_snapshot_consumo_itens, migrations.RunPython.noop),
    ]
