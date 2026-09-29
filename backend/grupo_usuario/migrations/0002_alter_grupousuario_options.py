from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('grupo_usuario', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='grupousuario',
            options={'managed': False},
        ),
    ]
