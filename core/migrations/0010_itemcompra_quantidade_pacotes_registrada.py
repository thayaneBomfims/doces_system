from decimal import Decimal

from django.db import migrations, models


def preencher_quantidade_pacotes_registrada(apps, schema_editor):
    ItemCompra = apps.get_model('core', 'ItemCompra')

    itens = ItemCompra.objects.select_related('ingrediente').all()
    for item in itens:
        gramas_unidade = Decimal(item.ingrediente.gramas_por_unidade or 0)
        if gramas_unidade > 0:
            item.quantidade_pacotes_registrada = Decimal(item.quantidade) / gramas_unidade
        else:
            item.quantidade_pacotes_registrada = Decimal('0')
        item.save(update_fields=['quantidade_pacotes_registrada'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_itempedido_custo_unitario_producao'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemcompra',
            name='quantidade_pacotes_registrada',
            field=models.DecimalField(decimal_places=4, default=0, max_digits=12),
        ),
        migrations.RunPython(preencher_quantidade_pacotes_registrada, migrations.RunPython.noop),
    ]
