import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Notificacao',
            fields=[
                ('id_notificacao', models.BigAutoField(db_column='id', primary_key=True, serialize=False)),
                ('tipo', models.CharField(max_length=40)),
                ('titulo', models.CharField(max_length=150)),
                ('mensagem', models.TextField()),
                ('lida', models.BooleanField(default=False)),
                ('dt_criacao', models.DateTimeField(db_column='data_criacao', default=django.utils.timezone.now)),
                ('dt_leitura', models.DateTimeField(blank=True, db_column='data_leitura', null=True)),
            ],
            options={
                'db_table': 'notificacao',
                'managed': False,
            },
        ),
    ]
