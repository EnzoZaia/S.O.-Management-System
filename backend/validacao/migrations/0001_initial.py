import django.utils.timezone
import validacao.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EvidenciaValidacao',
            fields=[
                ('id_evidencia', models.BigAutoField(db_column='id', primary_key=True, serialize=False)),
                ('arquivo', models.FileField(db_column='caminho_arquivo', max_length=255, upload_to=validacao.models._caminho_evidencia)),
                ('nome_original', models.CharField(max_length=255)),
                ('dt_upload', models.DateTimeField(db_column='data_upload', default=django.utils.timezone.now)),
            ],
            options={
                'db_table': 'evidencia_validacao',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='ValidacaoAtendimento',
            fields=[
                ('id_validacao', models.AutoField(db_column='id', primary_key=True, serialize=False)),
                ('resultado', models.CharField(blank=True, max_length=20, null=True)),
                ('justificativa', models.TextField(blank=True, null=True)),
                ('nota', models.SmallIntegerField(blank=True, null=True)),
                ('comentario', models.TextField(blank=True, null=True)),
                ('dt_validacao', models.DateTimeField(db_column='data_validacao', default=django.utils.timezone.now)),
            ],
            options={
                'db_table': 'validacao_atendimento',
                'managed': False,
            },
        ),
    ]
