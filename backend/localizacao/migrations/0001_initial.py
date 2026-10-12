from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Localizacao',
            fields=[
                ('id_localizacao', models.AutoField(db_column='id', primary_key=True, serialize=False)),
                ('desc_localizacao', models.CharField(db_column='nome', max_length=100)),
            ],
            options={
                'db_table': 'localizacao',
                'managed': False,
            },
        ),
    ]
