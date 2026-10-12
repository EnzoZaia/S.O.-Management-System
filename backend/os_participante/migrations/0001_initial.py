import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='OsParticipante',
            fields=[
                ('id_os_participante', models.BigAutoField(db_column='id', primary_key=True, serialize=False)),
                ('dt_vinculo', models.DateTimeField(db_column='data_vinculo', default=django.utils.timezone.now)),
            ],
            options={
                'db_table': 'os_participante',
                'managed': False,
            },
        ),
    ]
