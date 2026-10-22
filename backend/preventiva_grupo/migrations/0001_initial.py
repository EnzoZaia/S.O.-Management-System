from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ChecklistItemAtivo',
            fields=[
                ('id_checklist_item', models.BigAutoField(db_column='id', primary_key=True, serialize=False)),
                ('codigo_item', models.IntegerField()),
                ('descricao', models.CharField(max_length=255)),
                ('resultado', models.CharField(default='PENDENTE', max_length=20)),
                ('motivo', models.TextField(blank=True, null=True)),
                ('dt_resposta', models.DateTimeField(blank=True, db_column='data_resposta', null=True)),
            ],
            options={
                'db_table': 'checklist_item_ativo',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='OrdemServicoAtivo',
            fields=[
                ('id_ordem_servico_ativo', models.BigAutoField(db_column='id', primary_key=True, serialize=False)),
                ('resultado', models.CharField(default='PENDENTE', max_length=20)),
                ('motivo', models.TextField(blank=True, null=True)),
                ('dt_resultado', models.DateTimeField(blank=True, db_column='data_resultado', null=True)),
            ],
            options={
                'db_table': 'ordem_servico_ativo',
                'managed': False,
            },
        ),
    ]
