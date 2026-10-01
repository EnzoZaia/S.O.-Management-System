from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Predio',
            fields=[
                ('id_predio', models.BigAutoField(primary_key=True, serialize=False)),
                ('nome_predio', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'predio',
                'managed': True,
            },
        ),
    ]
