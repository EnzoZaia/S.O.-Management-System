from django.db import models
from usuario.models import Usuario
from grupo.models import Grupo

class GrupoUsuario(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='id_usuario', primary_key=True)
    grupo = models.ForeignKey(Grupo,on_delete=models.CASCADE, db_column='id_grupo')

    class Meta:
        managed = False
        #managed = True # Indica que o Django deve criar e gerenciar a tabela no banco de dados
        db_table = 'grupo_usuario'
        unique_together = (('usuario', 'grupo'),)

    def __str__(self):
        return f'{self.usuario} - {self.grupo}'