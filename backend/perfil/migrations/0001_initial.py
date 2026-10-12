import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('usuario', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Gerente',
            fields=[
                ('usuario', models.OneToOneField(db_column='usuario_id', on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='perfil_gerente', serialize=False, to='usuario.usuario')),
            ],
            options={
                'db_table': 'gerente',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Gestor',
            fields=[
                ('usuario', models.OneToOneField(db_column='usuario_id', on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='perfil_gestor', serialize=False, to='usuario.usuario')),
                ('area_atuacao', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'gestor',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Solicitante',
            fields=[
                ('usuario', models.OneToOneField(db_column='usuario_id', on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='perfil_solicitante', serialize=False, to='usuario.usuario')),
                ('tipo_vinculo', models.CharField(max_length=20)),
                ('identificador_vinculo', models.CharField(max_length=30)),
            ],
            options={
                'db_table': 'solicitante',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Tecnico',
            fields=[
                ('usuario', models.OneToOneField(db_column='usuario_id', on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='perfil_tecnico', serialize=False, to='usuario.usuario')),
                ('area_atuacao', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'tecnico',
                'managed': False,
            },
        ),
    ]
