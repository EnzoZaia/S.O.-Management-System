from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ativo', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ManualAtivo',
            fields=[
                ('id_manual', models.AutoField(db_column='id', primary_key=True, serialize=False)),
                ('titulo', models.CharField(max_length=150)),
                ('versao', models.CharField(blank=True, max_length=30, null=True)),
                ('caminho_arquivo', models.TextField()),
                ('ativo_para_consulta', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'manual_ativo',
                'managed': False,
            },
        ),
    ]
