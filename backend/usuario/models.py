from django.db import models
from django.contrib.auth.models import AbstractBaseUser

# Create your models here.
class Usuario(models.Model):
    # Modelo para representar um usuário no sistema/banco de dados 
    id_usuario = models.BigAutoField(primary_key=True)
    nome = models.CharField(max_length=150)
    email = models.CharField(max_length=150, unique=True)
    senha_hash = models.CharField(max_length=255)

    email_confirmado = models.BooleanField(default=False)
    token_confirmacao_email = models.CharField(max_length=255, null=True, blank=True)
    dt_expiracao_token = models.DateTimeField(null=True, blank=True)

    # Propriedade para indicar que o usuário está autenticado (sempre retorna True, pois é um modelo de usuário personalizado)
    @property
    def is_authenticated(self):
        return True # Como não usamos o modelo padrão do Django, precisamos garantir que o request.user seja tratado como autenticado nas permissões do DRF.

    class Meta:
        managed = False # Indica que o Django não deve criar ou gerenciar a tabela no banco de dados pq o banco de dados foi criado externamente (Supabase)
        #managed = True # Indica que o Django deve criar e gerenciar a tabela no banco de dados
        db_table = 'usuario'

    # Método para retornar uma representação legível do objeto, neste caso, o nome do usuário.
    def __str__(self):
        return self.nome