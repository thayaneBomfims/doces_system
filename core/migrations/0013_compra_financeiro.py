from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_itempedidoconsumo'),
    ]

    operations = [
        migrations.AddField(
            model_name='compra',
            name='desconto',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='compra',
            name='frete',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='compra',
            name='total_calculado',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='compra',
            name='total_final',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='compra',
            name='total_ingredientes',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
    ]
