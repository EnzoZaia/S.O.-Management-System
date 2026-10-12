from django.db import models
from usuario.models import Usuario

TIPO_VINCULO_ALUNO = 'ALUNO'
TIPO_VINCULO_FUNCIONARIO = 'FUNCIONARIO'


class Gerente(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, primary_key=True, db_column='usuario_id', related_name='perfil_gerente')

    class Meta:
        managed = False
        db_table = 'gerente'


class Gestor(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, primary_key=True, db_column='usuario_id', related_name='perfil_gestor')
    area_atuacao = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'gestor'


class Tecnico(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, primary_key=True, db_column='usuario_id', related_name='perfil_tecnico')
    area_atuacao = models.CharField(max_length=100)
    gestor = models.ForeignKey(Gestor, on_delete=models.DO_NOTHING, null=True, blank=True, db_column='gestor_id', related_name='tecnicos')

    class Meta:
        managed = False
        db_table = 'tecnico'


class Solicitante(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, primary_key=True, db_column='usuario_id', related_name='perfil_solicitante')
    tipo_vinculo = models.CharField(max_length=20)
    identificador_vinculo = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'solicitante'
        constraints = [
            models.UniqueConstraint(fields=['tipo_vinculo', 'identificador_vinculo'], name='solicitante_tipo_identificador_vinculo_key'),
        ]
