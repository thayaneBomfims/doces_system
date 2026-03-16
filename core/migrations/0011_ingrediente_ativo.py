from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_itemcompra_quantidade_pacotes_registrada'),
    ]

    operations = [
        migrations.AddField(
            model_name='ingrediente',
            name='ativo',
            field=models.BooleanField(default=True),
        ),
    ]
