from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ativo', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ativo',
            name='data_instalacao',
        ),
    ]
