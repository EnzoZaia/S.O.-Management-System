from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='OrdemServico',
            fields=[
                ('id_ordem_servico', models.AutoField(db_column='id', primary_key=True, serialize=False)),
                ('id_solicitacao', models.IntegerField(blank=True, db_column='solicitacao_id', null=True, unique=True)),
                ('tipo_manutencao', models.CharField(default='CORRETIVA', max_length=30)),
                ('categoria_manutencao', models.CharField(blank=True, max_length=50, null=True)),
                ('prioridade_urgencia', models.CharField(db_column='prioridade', default='NORMAL', max_length=20)),
                ('status_ordem_servico', models.CharField(db_column='status', default='EM_TRIAGEM', max_length=30)),
                ('descricao_servico', models.TextField()),
                ('causa_raiz', models.TextField(blank=True, null=True)),
                ('dt_abertura', models.DateTimeField(db_column='data_abertura')),
                ('dt_conclusao', models.DateTimeField(blank=True, db_column='data_conclusao', null=True)),
            ],
            options={
                'db_table': 'ordem_servico',
                'managed': False,
            },
        ),
    ]
