from django.db import models
from django.contrib.auth.models import AbstractBaseUser

class Usuario(models.Model):
    id_usuario = models.BigAutoField(primary_key=True)
    nome = models.CharField(max_length=150)
    email = models.CharField(max_length=150, unique=True)
    senha_hash = models.CharField(max_length=255)

    email_confirmado = models.BooleanField(default=False)
    token_confirmacao_email = models.CharField(max_length=255, null=True, blank=True)
    dt_expiracao_token = models.DateTimeField(null=True, blank=True)

    @property
    def is_authenticated(self):
        return True

    class Meta:
        managed = False
        db_table = 'usuario'

    def __str__(self):
        return self.nome
