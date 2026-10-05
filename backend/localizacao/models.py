from django.db import models
from predio.models import Predio


class Localizacao(models.Model):
    id_localizacao = models.BigAutoField(
        primary_key=True,
        db_column="id",
    )

    predio = models.ForeignKey(
        Predio,
        on_delete=models.DO_NOTHING,
        db_column="predio_id",
    )

    desc_localizacao = models.CharField(
        max_length=100,
        db_column="nome",
    )

    class Meta:
        managed = False
        db_table = "localizacao"

    def __str__(self):
        return self.desc_localizacao