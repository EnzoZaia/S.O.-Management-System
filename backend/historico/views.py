from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from historico.models import Historico
from historico.serializers import HistoricoSerializer
from utils.permissions import usuario_tem_grupo

# Create your views here.
# View para listar o histórico de ordens de serviço
class HistoricoListView(generics.ListAPIView):
    serializer_class = HistoricoSerializer
    permission_classes = (IsAuthenticated)

    def get_queryset(self):
        usuario = self.request.user

        if usuario_tem_grupo(usuario, "GERENTE"):
            return Historico.objects.all().order_by('-data_registro')

        if usuario_tem_grupo(usuario, "GESTOR"):
            return Historico.objects.filter(ordem_servico__gestor=usuario).order_by('-data_registro')

        if usuario_tem_grupo(usuario, "TECNICO"):
            return Historico.objects.filter(ordem_servico__tecnico=usuario).order_by('-data_registro')

        return Historico.objects.filter(ordem_servico__solicitante=usuario).order_by('-data_registro')

# View para listar o histórico de uma ordem de serviço específica
class HistoricoOrdemServicoListView(generics.ListAPIView):
    serializer_class = HistoricoSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        usuario = self.request.user
        id_ordem_servico = self.kwargs.get("pk")

        queryset = Historico.objects.filter(ordem_servico_id=id_ordem_servico).order_by('data_registro')

        if usuario_tem_grupo(usuario, "GERENTE"):
            return queryset

        if usuario_tem_grupo(usuario, "GESTOR"):
            return queryset.filter(ordem_servico__gestor=usuario)

        if usuario_tem_grupo(usuario, "TECNICO"):
            return queryset.filter(ordem_servico__tecnico=usuario)

        return queryset.filter(ordem_servico__solicitante=usuario)