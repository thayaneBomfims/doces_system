from django.db import migrations, models


def popular_nome_produto(apps, schema_editor):
    ItemPedido = apps.get_model('core', 'ItemPedido')

    for item in ItemPedido.objects.select_related('produto').all():
        if item.produto and not item.produto_nome:
            item.produto_nome = item.produto.nome
            item.save(update_fields=['produto_nome'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_compra_financeiro'),
    ]

    operations = [
        migrations.AlterField(
            model_name='itempedido',
            name='produto',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, to='core.produto'),
        ),
        migrations.AddField(
            model_name='itempedido',
            name='produto_nome',
            field=models.CharField(default='', max_length=200),
        ),
        migrations.RunPython(popular_nome_produto, migrations.RunPython.noop),
    ]
