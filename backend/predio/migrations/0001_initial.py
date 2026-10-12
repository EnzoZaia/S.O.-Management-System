from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Predio',
            fields=[
                ('id_predio', models.AutoField(db_column='id', primary_key=True, serialize=False)),
                ('nome_predio', models.CharField(db_column='nome', max_length=100)),
            ],
            options={
                'db_table': 'predio',
                'managed': False,
            },
        ),
    ]
