from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('grupo_usuario', '0002_alter_grupousuario_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='grupousuario',
            options={'managed': True},
        ),
    ]
