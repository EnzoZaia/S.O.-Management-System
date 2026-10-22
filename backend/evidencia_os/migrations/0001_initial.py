import django.utils.timezone
import evidencia_os.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EvidenciaOrdem',
            fields=[
                ('id_evidencia_ordem', models.BigAutoField(db_column='id', primary_key=True, serialize=False)),
                ('sequencia', models.IntegerField()),
                ('tipo_arquivo', models.CharField(max_length=10)),
                ('tipo_conteudo', models.CharField(max_length=60)),
                ('arquivo', models.FileField(db_column='caminho_arquivo', max_length=255, upload_to=evidencia_os.models._caminho_evidencia_ordem)),
                ('nome_original', models.CharField(max_length=255)),
                ('tamanho_bytes', models.BigIntegerField()),
                ('dt_envio', models.DateTimeField(db_column='data_envio', default=django.utils.timezone.now)),
            ],
            options={
                'db_table': 'evidencia_ordem',
                'managed': False,
            },
        ),
    ]
