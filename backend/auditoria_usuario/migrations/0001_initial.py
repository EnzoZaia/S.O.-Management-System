import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AuditoriaUsuario',
            fields=[
                ('id_auditoria', models.BigAutoField(db_column='id', primary_key=True, serialize=False)),
                ('campo', models.CharField(max_length=50)),
                ('valor_anterior', models.CharField(blank=True, max_length=255, null=True)),
                ('valor_novo', models.CharField(blank=True, max_length=255, null=True)),
                ('dt_registro', models.DateTimeField(db_column='data_registro', default=django.utils.timezone.now)),
            ],
            options={
                'db_table': 'auditoria_usuario',
                'managed': False,
            },
        ),
    ]
