import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Historico',
            fields=[
                ('id_historico_ordem_servico', models.AutoField(db_column='id', primary_key=True, serialize=False)),
                ('data_registro', models.DateTimeField(default=django.utils.timezone.now)),
                ('desc_historico', models.TextField(blank=True, db_column='descricao', null=True)),
                ('status_anterior', models.CharField(blank=True, max_length=30, null=True)),
                ('status_novo', models.CharField(blank=True, max_length=30, null=True)),
                ('tipo_evento', models.CharField(blank=True, max_length=30, null=True)),
            ],
            options={
                'db_table': 'historico',
                'managed': False,
            },
        ),
    ]
