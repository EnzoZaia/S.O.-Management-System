from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Usuario',
            fields=[
                ('id_usuario', models.BigAutoField(primary_key=True, serialize=False)),
                ('nome', models.CharField(max_length=150)),
                ('email', models.CharField(max_length=150, unique=True)),
                ('senha_hash', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'usuario',
                'managed': True,
            },
        ),
    ]
