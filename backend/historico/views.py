from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from historico.models import Historico
from historico.serializers import HistoricoSerializer
from ordem_servico.acesso import resolver_fabrica_acesso


def _historico_no_escopo(usuario):
    ordens_visiveis = resolver_fabrica_acesso(usuario).criar_escopo_consulta().filtrar(usuario)
    return Historico.objects.filter(ordem_servico__in=ordens_visiveis.values('id_ordem_servico')).select_related('usuario', 'tecnico')


class HistoricoListView(generics.ListAPIView):
    serializer_class = HistoricoSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return _historico_no_escopo(self.request.user).order_by('-data_registro')

class HistoricoOrdemServicoListView(generics.ListAPIView):
    serializer_class = HistoricoSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        id_ordem_servico = self.kwargs.get("pk")
        return _historico_no_escopo(self.request.user).filter(ordem_servico_id=id_ordem_servico).order_by('data_registro')
