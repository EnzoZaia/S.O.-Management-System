from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Ativo',
            fields=[
                ('id_ativo', models.AutoField(db_column='id', primary_key=True, serialize=False)),
                ('codigo_patrimonial', models.CharField(max_length=50, unique=True)),
                ('tipo_ativo', models.CharField(choices=[('AR_CONDICIONADO', 'Ar Condicionado'), ('BEBEDOURO', 'Bebedouro')], max_length=30)),
                ('marca', models.CharField(blank=True, max_length=100, null=True)),
                ('modelo', models.CharField(blank=True, max_length=100, null=True)),
                ('numero_serial', models.CharField(blank=True, max_length=100, null=True)),
                ('periodicidade_preventiva_dias', models.IntegerField(default=90)),
                ('dt_ultima_preventiva', models.DateField(blank=True, db_column='data_ultima_preventiva', null=True)),
                ('dt_proxima_preventiva', models.DateField(blank=True, db_column='data_proxima_preventiva', null=True)),
            ],
            options={
                'db_table': 'ativo',
                'managed': False,
            },
        ),
    ]
