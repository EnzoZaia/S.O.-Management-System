from django.db import models

class Predio(models.Model):
    id_predio = models.BigAutoField(primary_key=True)
    nome_predio = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'predio'

    def __str__(self):
        return self.nome_predio
