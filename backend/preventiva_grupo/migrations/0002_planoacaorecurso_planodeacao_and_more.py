import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('preventiva_grupo', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlanoAcaoRecurso',
            fields=[
                ('pk', models.CompositePrimaryKey('plano_acao_id', 'recurso_id', blank=True, editable=False, primary_key=True, serialize=False)),
                ('quantidade', models.DecimalField(decimal_places=3, max_digits=12)),
            ],
            options={
                'db_table': 'plano_acao_recurso',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='PlanoDeAcao',
            fields=[
                ('id_plano_acao', models.AutoField(db_column='id', primary_key=True, serialize=False)),
                ('descricao', models.TextField()),
                ('dt_criacao', models.DateTimeField(db_column='data_criacao', default=django.utils.timezone.now)),
                ('dt_conclusao', models.DateTimeField(blank=True, db_column='data_conclusao', null=True)),
                ('status', models.CharField(default='PENDENTE', max_length=20)),
            ],
            options={
                'db_table': 'plano_de_acao',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='PlanoManutencaoPreventiva',
            fields=[
                ('id_plano_manutencao', models.AutoField(db_column='id', primary_key=True, serialize=False)),
                ('tipo_ativo', models.CharField(max_length=30)),
                ('ciclo_dias', models.IntegerField()),
                ('dt_criacao', models.DateTimeField(db_column='data_criacao', default=django.utils.timezone.now)),
                ('ativo_no_sistema', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'plano_manutencao_preventiva',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='RecursoManutencao',
            fields=[
                ('id_recurso', models.AutoField(db_column='id', primary_key=True, serialize=False)),
                ('nome', models.CharField(max_length=120)),
                ('tipo', models.CharField(max_length=20)),
                ('unidade_medida', models.CharField(max_length=20)),
            ],
            options={
                'db_table': 'recurso_manutencao',
                'managed': False,
            },
        ),
    ]
