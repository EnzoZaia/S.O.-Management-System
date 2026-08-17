from django.utils import timezone
from historico.models import Historico

def registrar_historico(ordem_servico, usuario, descricao):
    Historico.objects.create(ordem_servico=ordem_servico, usuario=usuario, data_registro=timezone.now(), desc_historico=descricao)