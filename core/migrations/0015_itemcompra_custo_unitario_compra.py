from decimal import Decimal

from django.db import migrations, models


def preencher_custo_unitario_compra(apps, schema_editor):
    ItemCompra = apps.get_model('core', 'ItemCompra')

    for item in ItemCompra.objects.all():
        pacotes = Decimal(item.quantidade_pacotes_registrada or 0)
        if pacotes > 0:
            item.custo_unitario_compra = Decimal(item.custo_total or 0) / pacotes
        else:
            item.custo_unitario_compra = Decimal('0')
        item.save(update_fields=['custo_unitario_compra'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_itempedido_produto_snapshot'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemcompra',
            name='custo_unitario_compra',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.RunPython(preencher_custo_unitario_compra, migrations.RunPython.noop),
    ]
