import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AssistenteTecnicoIA',
            fields=[
                ('id_assistente', models.IntegerField(db_column='id', default=1, primary_key=True, serialize=False)),
                ('provedor', models.CharField(max_length=100)),
                ('modelo', models.CharField(max_length=100)),
                ('disponivel', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'assistente_tecnico_ia',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='ConsultaAssistenteIA',
            fields=[
                ('id_consulta', models.AutoField(db_column='id', primary_key=True, serialize=False)),
                ('provedor_ia', models.CharField(blank=True, max_length=60, null=True)),
                ('modelo_ia', models.CharField(blank=True, max_length=60, null=True)),
                ('pergunta', models.TextField()),
                ('resposta', models.TextField(blank=True, null=True)),
                ('status', models.CharField(default='PENDENTE', max_length=20)),
                ('dt_consulta', models.DateTimeField(db_column='data_consulta', default=django.utils.timezone.now)),
            ],
            options={
                'db_table': 'consulta_assistente_ia',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='IndicadorGerencial',
            fields=[
                ('id_indicador', models.AutoField(db_column='id', primary_key=True, serialize=False)),
                ('tipo_ativo', models.CharField(blank=True, max_length=30, null=True)),
                ('tipo', models.CharField(max_length=40)),
                ('valor', models.DecimalField(decimal_places=4, max_digits=14)),
                ('dt_inicio_periodo', models.DateField(db_column='data_inicio_periodo')),
                ('dt_fim_periodo', models.DateField(db_column='data_fim_periodo')),
                ('dt_calculo', models.DateTimeField(db_column='data_calculo', default=django.utils.timezone.now)),
            ],
            options={
                'db_table': 'indicador_gerencial',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='InsightGerencial',
            fields=[
                ('id_insight', models.AutoField(db_column='id', primary_key=True, serialize=False)),
                ('dt_inicio_periodo', models.DateField(db_column='data_inicio_periodo')),
                ('dt_fim_periodo', models.DateField(db_column='data_fim_periodo')),
                ('provedor_ia', models.CharField(blank=True, max_length=60, null=True)),
                ('modelo_ia', models.CharField(blank=True, max_length=60, null=True)),
                ('conteudo', models.TextField(blank=True, null=True)),
                ('status', models.CharField(default='PENDENTE', max_length=20)),
                ('dt_geracao', models.DateTimeField(db_column='data_geracao', default=django.utils.timezone.now)),
            ],
            options={
                'db_table': 'insight_gerencial',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='InsightIndicador',
            fields=[
                ('pk', models.CompositePrimaryKey('insight_id', 'indicador_id', blank=True, editable=False, primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'insight_indicador',
                'managed': False,
            },
        ),
    ]
