from django.core.exceptions import ObjectDoesNotExist
from django.db import models

STATUS_CONTA_PENDENTE = 'PENDENTE'
STATUS_CONTA_ATIVA = 'ATIVA'
STATUS_CONTA_DESATIVADA = 'DESATIVADA'


class Usuario(models.Model):
    id_usuario = models.BigAutoField(primary_key=True, db_column='id')
    nome = models.CharField(max_length=150)
    email = models.CharField(max_length=150, unique=True)
    senha_hash = models.CharField(max_length=255)

    email_confirmado = models.BooleanField(default=False)
    token_confirmacao_email = models.CharField(max_length=255, null=True, blank=True)
    dt_expiracao_token = models.DateTimeField(null=True, blank=True, db_column='data_expiracao_token')

    status_conta = models.CharField(max_length=20, default=STATUS_CONTA_PENDENTE)

    @property
    def is_authenticated(self):
        return True

    @property
    def ativo(self):
        return self.status_conta != STATUS_CONTA_DESATIVADA

    @property
    def ra(self):
        if not self.pk:
            return None
        try:
            return self.perfil_solicitante.identificador_vinculo
        except ObjectDoesNotExist:
            return None

    class Meta:
        managed = False
        db_table = 'usuario'

    def __str__(self):
        return self.nome
