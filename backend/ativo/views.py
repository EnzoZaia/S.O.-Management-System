from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated

from ativo.models import Ativo
from ativo.serializers import AtivoSerializer
from utils.responses import resposta_sucesso, resposta_erro
from utils.permissions import IsGerente, IsGestor,IsGerenteOuGestorOuTecnico
from rest_framework.views import APIView
from ordem_servico.models import OrdemServico
from ordem_servico.serializers import OrdemServicoSerializer

class AtivoListCreateView(generics.ListCreateAPIView):
    queryset = Ativo.objects.all().order_by('id_ativo')
    serializer_class = AtivoSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsGerenteOuGestorOuTecnico()]

        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = Ativo.objects.all().order_by('id_ativo')

        localizacao = self.request.query_params.get('localizacao')
        tipo_ativo = self.request.query_params.get('tipo_ativo')

        if localizacao:
            queryset = queryset.filter(localizacao_id=localizacao)

        if tipo_ativo:
            queryset = queryset.filter(tipo_ativo=tipo_ativo)

        return queryset

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)

        return resposta_sucesso("Ativos listados com sucesso.", serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            ativo = serializer.save()

            return resposta_sucesso("Ativo cadastrado com sucesso.", AtivoSerializer(ativo).data, status.HTTP_201_CREATED)

        return resposta_erro("Erro ao cadastrar ativo.", serializer.errors)

class AtivoRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Ativo.objects.all()
    serializer_class = AtivoSerializer

    def get_permissions(self):
        if self.request.method in ['PATCH', 'PUT', 'DELETE']:
            return [IsAuthenticated(), IsGerenteOuGestorOuTecnico()]

        return [IsAuthenticated()]

    def retrieve(self, request, *args, **kwargs):
        ativo = self.get_object()
        serializer = self.get_serializer(ativo)

        return resposta_sucesso("Ativo encontrado com sucesso.", serializer.data)

    def update(self, request, *args, **kwargs):
        parcial = kwargs.pop("partial", False)
        ativo = self.get_object()

        serializer = self.get_serializer(ativo, data=request.data, partial=parcial)

        if serializer.is_valid():
            ativo = serializer.save()
            return resposta_sucesso("Ativo atualizado com sucesso.", AtivoSerializer(ativo).data)

        return resposta_erro("Erro ao atualizar ativo.", serializer.errors)

    def destroy(self, request, *args, **kwargs):
        ativo = self.get_object()
        ativo.delete()

        return resposta_sucesso("Ativo removido com sucesso.", None, status.HTTP_200_OK)

class AtivoHistoricoView(APIView):
    """
    Retorna todo o histórico de manutenções (Ordens de Serviço concluídas) 
    vinculadas a um ativo específico.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            historico = OrdemServico.objects.filter(
                ativo_id=pk, 
                status_ordem_servico__in=['CONCLUIDA', 'ENCERRADA']
            ).order_by('-dt_conclusao')

            serializer = OrdemServicoSerializer(historico, many=True)
            return resposta_sucesso("Histórico carregado com sucesso.", serializer.data)

        except Exception as e:
            return resposta_erro(f"Erro ao buscar histórico: {str(e)}", None)
