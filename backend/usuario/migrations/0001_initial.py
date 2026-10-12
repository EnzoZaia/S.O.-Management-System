from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Usuario',
            fields=[
                ('id_usuario', models.BigAutoField(db_column='id', primary_key=True, serialize=False)),
                ('nome', models.CharField(max_length=150)),
                ('email', models.CharField(max_length=150, unique=True)),
                ('senha_hash', models.CharField(max_length=255)),
                ('email_confirmado', models.BooleanField(default=False)),
                ('token_confirmacao_email', models.CharField(blank=True, max_length=255, null=True)),
                ('dt_expiracao_token', models.DateTimeField(blank=True, db_column='data_expiracao_token', null=True)),
                ('status_conta', models.CharField(default='PENDENTE', max_length=20)),
            ],
            options={
                'db_table': 'usuario',
                'managed': False,
            },
        ),
    ]
