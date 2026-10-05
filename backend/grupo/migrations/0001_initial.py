from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Grupo',
            fields=[
                ('id_grupo', models.BigAutoField(primary_key=True, serialize=False)),
                ('desc_grupo', models.CharField(max_length=150)),
                ('desc_permissao', models.CharField(blank=True, max_length=150, null=True)),
            ],
            options={
                'db_table': 'grupo',
                'managed': True,
            },
        ),
    ]
